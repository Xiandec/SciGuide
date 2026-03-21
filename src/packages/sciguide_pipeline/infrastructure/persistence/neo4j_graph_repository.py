"""Neo4j graph repository adapter."""

from __future__ import annotations

from collections.abc import Sequence
import json
from typing import Any

from ...domain.entities import TextChunk
from ...domain.exceptions import MissingDependencyError
from ...domain.repositories import GraphRepository


class Neo4jGraphRepository(GraphRepository):
    """Neo4j-backed repository for concept graph projection."""

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
                "CREATE INDEX sciguide_chunk_lookup IF NOT EXISTS "
                "FOR (c:Chunk) ON (c.namespace, c.chunk_id)"
            ),
            (
                "CREATE INDEX sciguide_concept_lookup IF NOT EXISTS "
                "FOR (n:Concept) ON (n.namespace, n.name)"
            ),
        ]
        with self._driver.session(database=self._database) as session:
            for statement in statements:
                session.run(statement)

    def upsert_chunks(self, chunks: Sequence[TextChunk]) -> None:
        """Upsert chunk nodes and concept relations."""
        with self._driver.session(database=self._database) as session:
            for chunk in chunks:
                session.execute_write(
                    self._replace_chunk_projection,
                    self._namespace,
                    chunk,
                )

    def score_chunks(
        self,
        query_concepts: Sequence[str],
        chunk_ids: Sequence[str],
    ) -> dict[str, float]:
        """Score chunks by direct concept matches and local graph neighbors."""
        if not chunk_ids:
            return {}

        if not query_concepts:
            return {chunk_id: 0.0 for chunk_id in chunk_ids}

        query = """
        UNWIND $chunk_ids AS chunk_id
        MATCH (chunk:Chunk {namespace: $namespace, chunk_id: chunk_id})
        OPTIONAL MATCH (chunk)-[:MENTIONS]->
            (concept:Concept {namespace: $namespace})
        WITH chunk, collect(DISTINCT concept.name) AS chunk_concepts
        OPTIONAL MATCH (chunk)-[:MENTIONS]->
            (concept:Concept {namespace: $namespace})
        OPTIONAL MATCH
            (concept)-[:CO_OCCURS_IN|PRECEDES_IN {namespace: $namespace}]-
            (neighbor:Concept {namespace: $namespace})
        WITH chunk, chunk_concepts,
             collect(DISTINCT neighbor.name) AS neighboring_concepts
        RETURN chunk.chunk_id AS chunk_id,
               size([name IN chunk_concepts WHERE name IN $query_concepts]) +
               size([
                   name IN neighboring_concepts
                   WHERE name IN $query_concepts
               ]) * 0.25
               AS score
        """
        with self._driver.session(database=self._database) as session:
            result = session.run(
                query,
                namespace=self._namespace,
                chunk_ids=list(chunk_ids),
                query_concepts=list(query_concepts),
            )
            scores = {
                str(record["chunk_id"]): float(record["score"])
                for record in result
            }

        return {
            chunk_id: scores.get(chunk_id, 0.0)
            for chunk_id in chunk_ids
        }

    def close(self) -> None:
        """Close the Neo4j driver."""
        self._driver.close()

    @classmethod
    def _replace_chunk_projection(
        cls,
        tx: Any,
        namespace: str,
        chunk: TextChunk,
    ) -> None:
        tx.run(
            """
            MATCH (chunk:Chunk {namespace: $namespace, chunk_id: $chunk_id})
            OPTIONAL MATCH (chunk)-[mentions:MENTIONS]->()
            DELETE mentions
            """,
            namespace=namespace,
            chunk_id=chunk.id,
        )
        tx.run(
            """
            MATCH ()-[relation {
                namespace: $namespace,
                chunk_id: $chunk_id
            }]->()
            WHERE type(relation) IN ["CO_OCCURS_IN", "PRECEDES_IN"]
            DELETE relation
            """,
            namespace=namespace,
            chunk_id=chunk.id,
        )
        tx.run(
            """
            MERGE (chunk:Chunk {namespace: $namespace, chunk_id: $chunk_id})
            SET chunk.document_id = $document_id,
                chunk.text = $text,
                chunk.metadata_json = $metadata_json,
                chunk.sequence_number = $sequence_number
            WITH chunk
            UNWIND $concepts AS concept_name
            MERGE (concept:Concept {namespace: $namespace, name: concept_name})
            MERGE (chunk)-[:MENTIONS]->(concept)
            """,
            namespace=namespace,
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            text=chunk.text,
            metadata_json=cls._serialize_mapping(chunk.metadata),
            sequence_number=chunk.sequence_number,
            concepts=list(chunk.concepts),
        )

        co_occurs = cls._build_pairs(chunk.concepts)
        if co_occurs:
            tx.run(
                """
                UNWIND $relations AS relation
                MERGE (source:Concept {
                    namespace: $namespace,
                    name: relation.source
                })
                MERGE (target:Concept {
                    namespace: $namespace,
                    name: relation.target
                })
                MERGE (source)-[:CO_OCCURS_IN {
                    namespace: $namespace,
                    chunk_id: $chunk_id
                }]->(target)
                """,
                namespace=namespace,
                chunk_id=chunk.id,
                relations=co_occurs,
            )

        ordered_relations = cls._build_ordered_pairs(chunk.concepts)
        if ordered_relations:
            tx.run(
                """
                UNWIND $relations AS relation
                MERGE (source:Concept {
                    namespace: $namespace,
                    name: relation.source
                })
                MERGE (target:Concept {
                    namespace: $namespace,
                    name: relation.target
                })
                MERGE (source)-[:PRECEDES_IN {
                    namespace: $namespace,
                    chunk_id: $chunk_id
                }]->(target)
                """,
                namespace=namespace,
                chunk_id=chunk.id,
                relations=ordered_relations,
            )

    @staticmethod
    def _build_pairs(concepts: Sequence[str]) -> list[dict[str, str]]:
        pairs: list[dict[str, str]] = []
        unique_concepts = list(dict.fromkeys(concepts))
        for left_index, source in enumerate(unique_concepts):
            for target in unique_concepts[left_index + 1:]:
                pairs.append({"source": source, "target": target})
                pairs.append({"source": target, "target": source})
        return pairs

    @staticmethod
    def _build_ordered_pairs(concepts: Sequence[str]) -> list[dict[str, str]]:
        pairs: list[dict[str, str]] = []
        for index, source in enumerate(concepts):
            for target in concepts[index + 1:]:
                if source != target:
                    pairs.append({"source": source, "target": target})
        unique_pairs = {
            (pair["source"], pair["target"]): pair
            for pair in pairs
        }
        return list(unique_pairs.values())

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
