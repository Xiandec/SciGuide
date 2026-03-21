"""LangChain-based text chunker."""

from __future__ import annotations

from collections.abc import Sequence

from ...domain.entities import SourceDocument, TextChunk
from ...domain.exceptions import MissingDependencyError
from ...domain.services import TextChunker


class LangChainTextChunker(TextChunker):
    """Recursive character splitter adapter."""

    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        try:
            from langchain_text_splitters import (
                RecursiveCharacterTextSplitter,
            )
        except ImportError as error:
            raise MissingDependencyError(
                "langchain-text-splitters is required for chunking."
            ) from error

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk_documents(
        self,
        documents: Sequence[SourceDocument],
    ) -> list[TextChunk]:
        """Split documents into indexed chunks."""
        chunks: list[TextChunk] = []

        for document in documents:
            source_metadata = dict(document.metadata)
            if document.source_name:
                source_metadata.setdefault("source_name", document.source_name)

            for index, text in enumerate(
                self._splitter.split_text(document.content)
            ):
                chunk_id = f"{document.document_id}:{index}"
                chunks.append(
                    TextChunk(
                        id=chunk_id,
                        document_id=document.document_id or "",
                        text=text,
                        sequence_number=index,
                        metadata=dict(source_metadata),
                    )
                )

        return chunks
