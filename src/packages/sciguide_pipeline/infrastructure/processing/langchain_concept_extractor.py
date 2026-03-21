"""LangChain prompt wrapper for extracting concepts with an LLM."""

from __future__ import annotations

from collections.abc import Sequence
import re

from ...domain.services import ChatModel, ConceptExtractor

_TOKEN_PATTERN = re.compile(
    r"[0-9A-Za-zА-Яа-яЁё]+(?:-[0-9A-Za-zА-Яа-яЁё]+)*"
)


class LangChainConceptExtractor(ConceptExtractor):
    """Extract concepts from text using a prompted LLM."""

    def __init__(
        self,
        chat_model: ChatModel,
        max_concepts: int = 8,
    ) -> None:
        self._chat_model = chat_model
        self._max_concepts = max_concepts

    def extract(self, text: str) -> Sequence[str]:
        """Return normalized concept strings."""
        if not text.strip():
            return []

        system_prompt = (
            "You extract scientific concepts for graph-guided retrieval. "
            "Respond with strict JSON in the form "
            '{"concepts": ["concept one", "concept two"]}. '
            "Concepts must be short noun phrases in lowercase."
        )
        user_prompt = (
            f"Extract up to {self._max_concepts} concepts from the text.\n\n"
            f"Text:\n{text}"
        )
        payload = self._chat_model.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        concepts = payload.get("concepts", [])
        normalized: list[str] = []
        for concept in concepts:
            value = str(concept).strip().lower()
            if value and value not in normalized:
                normalized.append(value)
        return normalized

    def extract_tokens(self, text: str) -> Sequence[str]:
        """Return normalized tokens for legacy compatibility."""
        tokens: list[str] = []
        for match in _TOKEN_PATTERN.finditer(text.lower()):
            token = match.group(0)
            if token not in tokens:
                tokens.append(token)
        return tokens
