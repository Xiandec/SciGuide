"""OpenRouter adapter backed by LangChain's OpenAI-compatible client."""

from __future__ import annotations

import json
from typing import Any

from ...domain.exceptions import MissingDependencyError
from ...domain.services import ChatModel


class OpenRouterChatModel(ChatModel):
    """Chat model adapter for OpenRouter."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        base_url: str = "https://openrouter.ai/api/v1",
        request_timeout: float = 60.0,
    ) -> None:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as error:
            raise MissingDependencyError(
                "langchain-openai is required for OpenRouter support."
            ) from error

        self._client = ChatOpenAI(
            api_key=api_key,
            model=model_name,
            base_url=base_url,
            timeout=request_timeout,
            default_headers={
                "HTTP-Referer": "https://sciguide.local",
                "X-Title": "SciGuide Pipeline",
            },
        )

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Generate JSON and parse it into a Python object."""
        response = self._client.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )
        content = getattr(response, "content", "")
        return self._parse_json_content(content)

    @staticmethod
    def _parse_json_content(content: Any) -> dict[str, Any]:
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(str(item))
            content = "".join(parts)

        if not isinstance(content, str):
            raise ValueError("LLM response content is not text.")

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1:
                raise ValueError(
                    "LLM response does not contain JSON."
                ) from None
            return json.loads(content[start:end + 1])
