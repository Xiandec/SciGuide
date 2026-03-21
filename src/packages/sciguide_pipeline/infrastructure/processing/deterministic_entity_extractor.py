"""Deterministic entity extraction heuristics."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import re

from ...domain.services import EntityExtractor

_TOKEN_PATTERN = re.compile(
    r"[0-9A-Za-zА-Яа-яЁё]+(?:-[0-9A-Za-zА-Яа-яЁё]+)*"
)
_FRAGMENT_PATTERN = re.compile(r"[^.!?;:\n\r()\[\]{}]+")
_WORD_PATTERN = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+")
_BASE_WEIGHTS = {
    1: 1.0,
    2: 1.8,
    3: 2.6,
    4: 3.3,
}
_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "без",
    "в",
    "во",
    "для",
    "до",
    "и",
    "из",
    "или",
    "к",
    "как",
    "на",
    "над",
    "не",
    "но",
    "о",
    "об",
    "от",
    "по",
    "под",
    "при",
    "с",
    "со",
    "что",
    "это",
}
_BOUNDARY_TOKENS = _STOPWORDS | {
    "allow",
    "allows",
    "build",
    "builds",
    "compare",
    "compares",
    "compute",
    "computes",
    "describe",
    "describes",
    "estimate",
    "estimates",
    "explain",
    "explains",
    "improve",
    "improves",
    "improved",
    "include",
    "includes",
    "link",
    "links",
    "linked",
    "measure",
    "measures",
    "predict",
    "predicts",
    "present",
    "presents",
    "provide",
    "provides",
    "rank",
    "ranks",
    "retrieve",
    "retrieves",
    "show",
    "shows",
    "study",
    "studies",
    "train",
    "trains",
    "use",
    "used",
    "uses",
    "using",
    "анализирует",
    "использует",
    "используются",
    "объясняет",
    "описывает",
    "показывает",
    "связывает",
    "содержит",
    "улучшает",
}


@dataclass(frozen=True)
class _Token:
    raw: str
    normalized: str
    start: int


@dataclass(frozen=True)
class _Candidate:
    phrase: str
    tokens: tuple[str, ...]
    score: float
    start: int


class DeterministicEntityExtractor(EntityExtractor):
    """Extract scientific entities with local token n-gram heuristics."""

    def __init__(
        self,
        *,
        max_ngram_size: int = 4,
        max_entities: int = 12,
    ) -> None:
        self._max_ngram_size = max_ngram_size
        self._max_entities = max_entities

    def extract(self, text: str) -> Sequence[str]:
        """Return a stable list of entity phrases ordered by appearance."""
        if not text.strip():
            return []

        deduplicated: dict[str, _Candidate] = {}
        for fragment_text, fragment_offset in self._iter_fragments(text):
            fragment_tokens = self._tokenize_with_offsets(
                fragment_text,
                base_offset=fragment_offset,
            )
            for candidate in self._build_candidates(fragment_tokens):
                existing = deduplicated.get(candidate.phrase)
                if existing is None or (
                    candidate.score > existing.score
                    or (
                        candidate.score == existing.score
                        and candidate.start < existing.start
                    )
                ):
                    deduplicated[candidate.phrase] = candidate

        ranked_candidates = sorted(
            deduplicated.values(),
            key=lambda item: (-item.score, -len(item.tokens), item.start),
        )

        selected: list[_Candidate] = []
        for candidate in ranked_candidates:
            if any(
                self._contains_subsequence(existing.tokens, candidate.tokens)
                for existing in selected
            ):
                continue
            selected.append(candidate)
            if len(selected) >= self._max_entities:
                break

        return [
            candidate.phrase
            for candidate in sorted(selected, key=lambda item: item.start)
        ]

    def extract_tokens(self, text: str) -> Sequence[str]:
        """Return normalized content tokens used for token-to-entity lookup."""
        unique_tokens: list[str] = []
        for match in _TOKEN_PATTERN.finditer(text):
            normalized = match.group(0).lower()
            if not self._is_index_token(normalized):
                continue
            if normalized not in unique_tokens:
                unique_tokens.append(normalized)
        return unique_tokens

    def _iter_fragments(self, text: str) -> Iterable[tuple[str, int]]:
        for match in _FRAGMENT_PATTERN.finditer(text):
            fragment = match.group(0).strip()
            if fragment:
                yield fragment, match.start()

    def _tokenize_with_offsets(
        self,
        text: str,
        *,
        base_offset: int,
    ) -> list[_Token]:
        tokens: list[_Token] = []
        for match in _TOKEN_PATTERN.finditer(text):
            raw = match.group(0)
            normalized = raw.lower()
            tokens.append(
                _Token(
                    raw=raw,
                    normalized=normalized,
                    start=base_offset + match.start(),
                )
            )
        return tokens

    def _build_candidates(
        self,
        fragment_tokens: Sequence[_Token],
    ) -> Iterable[_Candidate]:
        for token_run in self._split_token_runs(fragment_tokens):
            token_count = len(token_run)
            for start_index in range(token_count):
                for end_index in range(
                    start_index + 1,
                    min(token_count, start_index + self._max_ngram_size) + 1,
                ):
                    window = token_run[start_index:end_index]
                    if not self._is_candidate_window(window):
                        continue
                    normalized_tokens = tuple(
                        token.normalized for token in window
                    )
                    yield _Candidate(
                        phrase=" ".join(normalized_tokens),
                        tokens=normalized_tokens,
                        score=self._score_candidate(window),
                        start=window[0].start,
                    )

    def _split_token_runs(
        self,
        fragment_tokens: Sequence[_Token],
    ) -> Iterable[list[_Token]]:
        current_run: list[_Token] = []
        for token in fragment_tokens:
            if token.normalized in _BOUNDARY_TOKENS:
                if current_run:
                    yield current_run
                    current_run = []
                continue
            current_run.append(token)

        if current_run:
            yield current_run

    def _is_candidate_window(
        self,
        tokens: Sequence[_Token],
    ) -> bool:
        if not tokens:
            return False

        normalized_tokens = [token.normalized for token in tokens]
        if normalized_tokens[0] in _STOPWORDS:
            return False
        if normalized_tokens[-1] in _STOPWORDS:
            return False
        if all(token in _STOPWORDS for token in normalized_tokens):
            return False
        if len(tokens) == 1 and not self._is_salient_single_token(tokens[0]):
            return False
        return True

    def _is_salient_single_token(self, token: _Token) -> bool:
        normalized = token.normalized
        if any(character.isdigit() for character in normalized):
            return True
        if "-" in normalized:
            return True
        if token.raw.isupper() and len(normalized) >= 2:
            return True
        return len(normalized) >= 4 and normalized not in _STOPWORDS

    def _score_candidate(
        self,
        tokens: Sequence[_Token],
    ) -> float:
        token_values = [token.normalized for token in tokens]
        score = _BASE_WEIGHTS.get(len(tokens), float(len(tokens)))
        if any(
            any(character.isdigit() for character in token)
            for token in token_values
        ):
            score += 0.45
        if any("-" in token for token in token_values):
            score += 0.30
        score += sum(0.05 for token in token_values if len(token) >= 8)
        return score

    def _is_index_token(self, token: str) -> bool:
        if token in _STOPWORDS:
            return False
        if token in _BOUNDARY_TOKENS:
            return False
        if "-" in token:
            return True
        if any(character.isdigit() for character in token):
            return True
        return len(token) >= 3

    @staticmethod
    def _contains_subsequence(
        outer_tokens: Sequence[str],
        inner_tokens: Sequence[str],
    ) -> bool:
        if len(inner_tokens) >= len(outer_tokens):
            return False

        last_start = len(outer_tokens) - len(inner_tokens) + 1
        for start_index in range(last_start):
            if (
                tuple(
                    outer_tokens[
                        start_index : start_index + len(inner_tokens)
                    ]
                )
                == tuple(inner_tokens)
            ):
                return True
        return False

    @staticmethod
    def tokenize_phrase(phrase: str) -> list[str]:
        """Normalize phrase text into indexable tokens."""
        tokens: list[str] = []
        for match in _WORD_PATTERN.finditer(phrase.lower()):
            token = match.group(0)
            if token not in tokens:
                tokens.append(token)
        return tokens
