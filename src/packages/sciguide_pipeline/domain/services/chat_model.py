"""LLM contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ChatModel(ABC):
    """Abstraction over an LLM client used by the pipelines."""

    @abstractmethod
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Generate JSON output from the model."""
