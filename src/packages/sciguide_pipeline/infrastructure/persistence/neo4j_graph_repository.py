"""Neo4j graph repository adapter."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
import json
import math
from typing import Any

from ...domain.entities import TextChunk
from ...domain.exceptions import MissingDependencyError
from ...domain.repositories import GraphRepository
from ..processing.deterministic_entity_extractor import (
    DeterministicEntityExtractor,
)


class Neo4jGraphRepository(GraphRepository):
    """Neo4j-backed repository for entity graph projection."""

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str,
        namespace: str,
    ) -> None:
        try:
            from neo4j import GraphDatabase
        except ImportError as error:
            raise MissingDependencyError(
                "neo4j is required for graph storage."
            ) from error

        self._database = database
        self._namespace = namespace
        self._driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
        )

    @property
    def namespace(self) -> str:
        """Return the configured graph namespace."""
        return self._namespace

    def ensure_schema(self) -> None:
        """Create indexes used by the graph projection."""
        statements = [
            (
                "CREATE INDEX sciguide_document_lookup IF NOT EXISTS "
                "FOR (d:Document) ON (d.namespace, d.document_id)"
            ),
            (
                "CREATE INDEX sciguide_chunk_lookup IF NOT EXISTS "
                "FOR (c:Chunk) ON (c.namespace, c.chunk_id)"
            ),
            (
                "CREATE INDEX sciguide_entity_lookup IF NOT EXISTS "
                "FOR (e:Entity) ON (e.namespace, e.name)"
            ),
            (
                "CREATE INDEX sciguide_token_lookup IF NOT EXISTS "
                "FOR (t:Token) ON (t.namespace, t.value)"
            ),
        ]
        with self._driver.session(database=self._database) as session:
            for statement in statements:
                session.run(statement)

    def upsert_chunks(self, chunks: Sequence[TextChunk]) -> None:
        """Upsert document, chunk, and entity projections."""
        grouped_chunks = self._group_chunks_by_document(chunks)
        with self._driver.session(database=self._database) as session:
            for document_id, document_chunks in grouped_chunks.items():
                session.execute_write(
                    self._replace_document_projection,
                    self._namespace,
                    document_id,
                    document_chunks,
                )

    def score_chunks(
        self,
        query_entities: Sequence[str],
        query_tokens: Sequence[str],
        chunk_ids: Sequence[str],
    ) -> dict[str, float]:
        """Score chunks with exact matches, token overlap, and neighbors."""
        if not chunk_ids:
            return {}

        unique_query_entities = list(dict.fromkeys(query_entities))
        unique_query_tokens = list(dict.fromkeys(query_tokens))
        if not unique_query_entities and not unique_query_tokens:
            return {chunk_id: 0.0 for chunk_id in chunk_ids}

        with self._driver.session(database=self._database) as session:
            entity_scores = self._build_query_entity_scores(
                session=session,
                query_entities=unique_query_entities,
                query_tokens=unique_query_tokens,
            )
            if not entity_scores:
                return {chunk_id: 0.0 for chunk_id in chunk_ids}

            chunk_entities = self._fetch_chunk_entities(
                session=session,
                chunk_ids=chunk_ids,
            )

        scores: dict[str, float] = {}
        for chunk_id in chunk_ids:
            entities = chunk_entities.get(chunk_id, [])
            matched_scores = [
                entity_scores[entity]
                for entity in entities
                if entity in entity_scores
            ]
            if not matched_scores:
                scores[chunk_id] = 0.0
                continue

            scores[chunk_id] = sum(matched_scores) + (0.15 * len(matched_scores))

        return scores

    def close(self) -> None:
        """Close the Neo4j driver."""
        self._driver.close()

    @classmethod
    def _replace_document_projection(
        cls,
        tx: Any,
        namespace: str,
        document_id: str,
        chunks: Sequence[TextChunk],
    ) -> None:
        existing = tx.run(
            """
            MATCH (document:Document {
                namespace: $namespace,
                document_id: $document_id
            })
            RETURN document.entities AS entities,
                   document.order_pairs_json AS order_pairs_json
            """,
            namespace=namespace,
            document_id=document_id,
        ).single()

        if existing is not None:
            old_entities = list(existing.get("entities") or [])
            old_order_pairs = cls._deserialize_order_pairs(
                existing.get("order_pairs_json")
            )
            cls._remove_document_contributions(
                tx=tx,
                namespace=namespace,
                document_id=document_id,
                entity_names=old_entities,
                order_pairs=old_order_pairs,
            )

        tx.run(
            """
            MATCH (document:Document {
                namespace: $namespace,
                document_id: $document_id
            })
            OPTIONAL MATCH (document)-[:HAS_CHUNK]->(chunk:Chunk {
                namespace: $namespace
            })
            WITH document, collect(chunk) AS chunks
            FOREACH (chunk IN [item IN chunks WHERE item IS NOT NULL] |
                DETACH DELETE chunk
            )
            WITH DISTINCT document
            DETACH DELETE document
            """,
            namespace=namespace,
            document_id=document_id,
        )

        ordered_chunks = sorted(chunks, key=lambda chunk: chunk.sequence_number)
        document_entities = cls._collect_document_entities(ordered_chunks)
        order_pairs = cls._build_document_order_pairs(ordered_chunks)

        tx.run(
            """
            MERGE (document:Document {
                namespace: $namespace,
                document_id: $document_id
            })
            SET document.entities = $entities,
                document.order_pairs_json = $order_pairs_json
            """,
            namespace=namespace,
            document_id=document_id,
            entities=document_entities,
            order_pairs_json=cls._serialize_order_pairs(order_pairs),
        )

        for chunk in ordered_chunks:
            cls._upsert_chunk_projection(
                tx=tx,
                namespace=namespace,
                document_id=document_id,
                chunk=chunk,
            )

        entity_payload = [
            {
                "name": entity_name,
                "tokens": DeterministicEntityExtractor.tokenize_phrase(
                    entity_name
                ),
            }
            for entity_name in document_entities
        ]
        if entity_payload:
            tx.run(
                """
                UNWIND $entities AS entity_data
                MERGE (entity:Entity {
                    namespace: $namespace,
                    name: entity_data.name
                })
                SET entity.tokens = entity_data.tokens
                WITH entity, entity_data
                SET entity.document_ids =
                    CASE
                        WHEN entity.document_ids IS NULL THEN [$document_id]
                        WHEN $document_id IN entity.document_ids
                            THEN entity.document_ids
                        ELSE entity.document_ids + $document_id
                    END
                WITH entity, entity_data
                SET entity.doc_count = size(entity.document_ids)
                WITH entity, entity_data
                MATCH (document:Document {
                    namespace: $namespace,
                    document_id: $document_id
                })
                MERGE (document)-[:HAS_ENTITY]->(entity)
                WITH entity, entity_data
                UNWIND entity_data.tokens AS token_value
                MERGE (token:Token {
                    namespace: $namespace,
                    value: token_value
                })
                MERGE (token)-[:TOKEN_OF]->(entity)
                """,
                namespace=namespace,
                document_id=document_id,
                entities=entity_payload,
            )

        order_payload = [
            {
                "source": source,
                "target": target,
                "weight": weight,
            }
            for (source, target), weight in order_pairs.items()
        ]
        if order_payload:
            tx.run(
                """
                UNWIND $pairs AS pair
                MERGE (source:Entity {
                    namespace: $namespace,
                    name: pair.source
                })
                MERGE (target:Entity {
                    namespace: $namespace,
                    name: pair.target
                })
                MERGE (source)-[relation:PRECEDES {
                    namespace: $namespace
                }]->(target)
                ON CREATE SET relation.weight = pair.weight
                ON MATCH SET relation.weight = relation.weight + pair.weight
                """,
                namespace=namespace,
                pairs=order_payload,
            )

    @classmethod
    def _upsert_chunk_projection(
        cls,
        tx: Any,
        namespace: str,
        document_id: str,
        chunk: TextChunk,
    ) -> None:
        tx.run(
            """
            MATCH (document:Document {
                namespace: $namespace,
                document_id: $document_id
            })
            MERGE (chunk:Chunk {
                namespace: $namespace,
                chunk_id: $chunk_id
            })
            SET chunk.document_id = $document_id,
                chunk.text = $text,
                chunk.metadata_json = $metadata_json,
                chunk.sequence_number = $sequence_number,
                chunk.entities = $entities
            MERGE (document)-[:HAS_CHUNK]->(chunk)
            WITH chunk
            UNWIND $entities AS entity_name
            MERGE (entity:Entity {
                namespace: $namespace,
                name: entity_name
            })
            MERGE (chunk)-[:MENTIONS]->(entity)
            """,
            namespace=namespace,
            document_id=document_id,
            chunk_id=chunk.id,
            text=chunk.text,
            metadata_json=cls._serialize_mapping(chunk.metadata),
            sequence_number=chunk.sequence_number,
            entities=list(chunk.entities),
        )

    @classmethod
    def _remove_document_contributions(
        cls,
        tx: Any,
        namespace: str,
        document_id: str,
        entity_names: Sequence[str],
        order_pairs: dict[tuple[str, str], int],
    ) -> None:
        for (source, target), weight in order_pairs.items():
            tx.run(
                """
                MATCH (source:Entity {
                    namespace: $namespace,
                    name: $source
                })-[relation:PRECEDES {
                    namespace: $namespace
                }]->(target:Entity {
                    namespace: $namespace,
                    name: $target
                })
                SET relation.weight = relation.weight - $weight
                WITH relation
                WHERE relation.weight <= 0
                DELETE relation
                """,
                namespace=namespace,
                source=source,
                target=target,
                weight=weight,
            )

        for entity_name in entity_names:
            tx.run(
                """
                MATCH (entity:Entity {
                    namespace: $namespace,
                    name: $entity_name
                })
                WITH entity,
                     [
                         doc_id
                         IN coalesce(entity.document_ids, [])
                         WHERE doc_id <> $document_id
                     ] AS remaining_doc_ids
                SET entity.document_ids = remaining_doc_ids,
                    entity.doc_count = size(remaining_doc_ids)
                WITH entity
                WHERE entity.doc_count = 0
                DETACH DELETE entity
                """,
                namespace=namespace,
                entity_name=entity_name,
                document_id=document_id,
            )

        tx.run(
            """
            MATCH (token:Token {namespace: $namespace})
            WHERE NOT (token)-[:TOKEN_OF]->(:Entity {namespace: $namespace})
            DELETE token
            """,
            namespace=namespace,
        )

    def _build_query_entity_scores(
        self,
        *,
        session: Any,
        query_entities: Sequence[str],
        query_tokens: Sequence[str],
    ) -> dict[str, float]:
        entity_scores: dict[str, float] = {}

        for entity_name in query_entities:
            entity_scores[entity_name] = max(
                entity_scores.get(entity_name, 0.0),
                2.0,
            )

        if query_tokens:
            token_matches = session.run(
                """
                UNWIND $query_tokens AS query_token
                MATCH (token:Token {
                    namespace: $namespace,
                    value: query_token
                })-[:TOKEN_OF]->(entity:Entity {namespace: $namespace})
                WITH entity, collect(DISTINCT query_token) AS matched_tokens
                RETURN entity.name AS entity_name,
                       coalesce(entity.tokens, []) AS entity_tokens,
                       matched_tokens
                """,
                namespace=self._namespace,
                query_tokens=list(query_tokens),
            )
            for record in token_matches:
                entity_name = str(record["entity_name"])
                entity_tokens = list(record["entity_tokens"] or [])
                matched_tokens = list(record["matched_tokens"] or [])
                if not entity_tokens or not matched_tokens:
                    continue
                overlap_ratio = len(matched_tokens) / len(entity_tokens)
                entity_scores[entity_name] = max(
                    entity_scores.get(entity_name, 0.0),
                    0.75 + overlap_ratio,
                )

        seed_entities = list(entity_scores)
        if seed_entities:
            neighbor_matches = session.run(
                """
                UNWIND $seed_entities AS seed_entity
                MATCH (seed:Entity {
                    namespace: $namespace,
                    name: seed_entity
                })
                MATCH (seed)-[relation:PRECEDES {
                    namespace: $namespace
                }]-(neighbor:Entity {namespace: $namespace})
                RETURN neighbor.name AS entity_name,
                       sum(relation.weight) AS total_weight
                """,
                namespace=self._namespace,
                seed_entities=seed_entities,
            )
            for record in neighbor_matches:
                entity_name = str(record["entity_name"])
                total_weight = float(record["total_weight"] or 0.0)
                if total_weight <= 0.0:
                    continue
                entity_scores[entity_name] = (
                    entity_scores.get(entity_name, 0.0)
                    + min(math.log1p(total_weight), 2.0) * 0.35
                )

        return entity_scores

    def _fetch_chunk_entities(
        self,
        *,
        session: Any,
        chunk_ids: Sequence[str],
    ) -> dict[str, list[str]]:
        records = session.run(
            """
            UNWIND $chunk_ids AS chunk_id
            MATCH (chunk:Chunk {
                namespace: $namespace,
                chunk_id: chunk_id
            })
            RETURN chunk.chunk_id AS chunk_id,
                   coalesce(chunk.entities, []) AS entities
            """,
            namespace=self._namespace,
            chunk_ids=list(chunk_ids),
        )
        return {
            str(record["chunk_id"]): list(record["entities"] or [])
            for record in records
        }

    @staticmethod
    def _group_chunks_by_document(
        chunks: Sequence[TextChunk],
    ) -> dict[str, list[TextChunk]]:
        grouped: dict[str, list[TextChunk]] = defaultdict(list)
        for chunk in chunks:
            grouped[chunk.document_id].append(chunk)
        return grouped

    @staticmethod
    def _collect_document_entities(
        chunks: Sequence[TextChunk],
    ) -> list[str]:
        ordered_entities: list[str] = []
        seen_entities: set[str] = set()
        for chunk in chunks:
            for entity_name in chunk.entities:
                if entity_name in seen_entities:
                    continue
                seen_entities.add(entity_name)
                ordered_entities.append(entity_name)
        return ordered_entities

    @staticmethod
    def _build_document_order_pairs(
        chunks: Sequence[TextChunk],
    ) -> dict[tuple[str, str], int]:
        pair_weights: dict[tuple[str, str], int] = defaultdict(int)
        for chunk in chunks:
            unique_entities = list(dict.fromkeys(chunk.entities))
            for index, left_entity in enumerate(unique_entities):
                right_boundary = min(len(unique_entities), index + 3)
                for right_index in range(index + 1, right_boundary):
                    right_entity = unique_entities[right_index]
                    if left_entity == right_entity:
                        continue
                    pair_weights[(left_entity, right_entity)] += 1
        return dict(pair_weights)

    @staticmethod
    def _serialize_order_pairs(
        order_pairs: dict[tuple[str, str], int],
    ) -> str:
        payload = [
            {
                "source": source,
                "target": target,
                "weight": weight,
            }
            for (source, target), weight in sorted(order_pairs.items())
        ]
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _deserialize_order_pairs(
        payload: str | None,
    ) -> dict[tuple[str, str], int]:
        if not payload:
            return {}
        parsed = json.loads(payload)
        order_pairs: dict[tuple[str, str], int] = {}
        for item in parsed:
            source = str(item["source"])
            target = str(item["target"])
            weight = int(item["weight"])
            order_pairs[(source, target)] = weight
        return order_pairs

    @classmethod
    def _sanitize_mapping(cls, mapping: dict[str, Any]) -> dict[str, Any]:
        return {
            key: cls._sanitize_value(value)
            for key, value in mapping.items()
        }

    @classmethod
    def _sanitize_value(cls, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return cls._sanitize_mapping(value)
        if isinstance(value, (list, tuple, set)):
            return [cls._sanitize_value(item) for item in value]
        return str(value)

    @classmethod
    def _serialize_mapping(cls, mapping: dict[str, Any]) -> str:
        return json.dumps(
            cls._sanitize_mapping(mapping),
            ensure_ascii=False,
            sort_keys=True,
        )
