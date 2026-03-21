"""Assistant responder backed by OpenRouter with retrieval fallback."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from typing import Any
from uuid import UUID

import httpx
from sciguide_pipeline import PipelineManager

from config import settings
from messages.domain.entities.message import Message
from messages.domain.entities.message import MessageContextDocument
from messages.domain.entities.message import MessageRole
from messages.domain.exceptions.message_exceptions import (
    MessageGenerationError,
)
from messages.domain.services.assistant_responder import AssistantResponder
from messages.domain.services.assistant_responder import AssistantResponse
from messages.domain.services.assistant_responder import (
    AssistantResponderRequest,
)


class OpenRouterAssistantResponder(AssistantResponder):
    """Generate assistant answers using retrieval and OpenRouter."""

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        base_url: str,
        request_timeout_seconds: float,
        search_limit: int = 5,
        candidate_limit: int = 20,
        history_limit: int = 12,
    ) -> None:
        self._api_key = api_key.strip()
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._request_timeout_seconds = request_timeout_seconds
        self._search_limit = search_limit
        self._candidate_limit = candidate_limit
        self._history_limit = history_limit

    async def generate(
        self,
        request: AssistantResponderRequest,
    ) -> AssistantResponse:
        """Generate an assistant response for one chat turn."""
        documents_used, snippets = await asyncio.to_thread(
            self._retrieve_context,
            request.workspace_id,
            request.user_message_content,
        )

        if self._api_key:
            try:
                content = await self._generate_with_llm(
                    request=request,
                    snippets=snippets,
                )
                return AssistantResponse(
                    content=content,
                    documents_used=tuple(documents_used),
                )
            except Exception as exc:
                if not snippets:
                    raise MessageGenerationError(
                        str(exc) or "LLM request failed",
                    ) from exc
                return AssistantResponse(
                    content=self._build_fallback_response(
                        user_message_content=request.user_message_content,
                        snippets=snippets,
                    ),
                    documents_used=tuple(documents_used),
                )

        if snippets:
            return AssistantResponse(
                content=self._build_fallback_response(
                    user_message_content=request.user_message_content,
                    snippets=snippets,
                ),
                documents_used=tuple(documents_used),
            )

        raise MessageGenerationError(
            "No LLM API key configured and no retrieval context was found",
        )

    def _retrieve_context(
        self,
        workspace_id: UUID,
        query: str,
    ) -> tuple[list[MessageContextDocument], list[str]]:
        """Run retrieval over workspace documents and normalize snippets."""
        collection_name = (
            f"{settings.qdrant_collection_prefix}{workspace_id.hex}"
        )
        try:
            with PipelineManager(
                qdrant_url=settings.qdrant_url,
                qdrant_collection_name=collection_name,
                neo4j_uri=settings.pipeline_neo4j_uri,
                neo4j_username=settings.neo4j_username,
                neo4j_password=settings.neo4j_password,
                embedding_model_name=settings.pipeline_embedding_model_name,
                reranker_model_name=settings.pipeline_reranker_model_name,
                model_cache_dir=settings.pipeline_model_cache_dir,
                graph_namespace=collection_name,
                qdrant_api_key=settings.qdrant_api_key,
                qdrant_prefer_grpc=settings.qdrant_prefer_grpc,
                neo4j_database=settings.neo4j_database,
                huggingface_token=settings.huggingface_token,
                chunk_size=settings.pipeline_chunk_size,
                chunk_overlap=settings.pipeline_chunk_overlap,
                search_limit=self._search_limit,
                search_candidate_limit=self._candidate_limit,
                request_timeout=settings.pipeline_request_timeout_seconds,
            ) as manager:
                report = manager.search.run(
                    query=query,
                    limit=self._search_limit,
                    candidate_limit=self._candidate_limit,
                )
        except Exception as exc:
            raise MessageGenerationError(
                "Workspace retrieval failed. Check pipeline indexing and "
                "vector collection configuration."
            ) from exc

        documents_by_id: OrderedDict[str, MessageContextDocument] = (
            OrderedDict()
        )
        snippets: list[str] = []
        for index, item in enumerate(report.items, start=1):
            filename = str(item.metadata.get("filename", "document"))
            document_id = item.document_id.strip()
            if document_id and document_id not in documents_by_id:
                try:
                    documents_by_id[document_id] = MessageContextDocument(
                        document_id=UUID(document_id),
                        filename=filename,
                        rank=len(documents_by_id) + 1,
                        excerpt=item.text[:500],
                    )
                except ValueError:
                    continue

            snippet_text = item.text.strip()
            if snippet_text:
                snippets.append(f"[{index}] {filename}: {snippet_text[:1200]}")

        return list(documents_by_id.values()), snippets

    async def _generate_with_llm(
        self,
        *,
        request: AssistantResponderRequest,
        snippets: list[str],
    ) -> str:
        """Call OpenRouter chat completions and normalize the answer."""
        system_prompt = self._build_system_prompt(request.workspace_prompt)
        user_prompt = self._build_user_prompt(
            history=request.message_history,
            user_message_content=request.user_message_content,
            snippets=snippets,
        )

        async with httpx.AsyncClient(
            timeout=self._request_timeout_seconds,
        ) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "HTTP-Referer": "https://sciguide.local",
                    "X-Title": "SciGuide Backend",
                },
                json={
                    "model": self._model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            payload = response.json()

        content = self._extract_message_content(payload)
        normalized = content.strip()
        if not normalized:
            raise MessageGenerationError("LLM returned an empty response")
        return normalized[:20_000]

    def _build_system_prompt(self, workspace_prompt: str) -> str:
        """Compose the system prompt for assistant generation."""
        return (
            f"{workspace_prompt.strip()}\n\n"
            "Use only the current workspace context and the provided chat "
            "history. If the workspace context is insufficient, say so "
            "explicitly and do not invent facts."
        )

    def _build_user_prompt(
        self,
        *,
        history: tuple[Message, ...],
        user_message_content: str,
        snippets: list[str],
    ) -> str:
        """Compose a single user prompt for the chat completion call."""
        history_lines = []
        for item in history[-self._history_limit:]:
            role_label = (
                "User"
                if item.role == MessageRole.USER
                else "Assistant"
            )
            history_lines.append(f"{role_label}: {item.content.strip()}")

        joined_history = "\n".join(history_lines) or "No previous messages."
        joined_snippets = (
            "\n\n".join(snippets) or "No relevant snippets found."
        )
        return (
            "Chat history:\n"
            f"{joined_history}\n\n"
            "Workspace retrieval context:\n"
            f"{joined_snippets}\n\n"
            "Current user question:\n"
            f"{user_message_content}"
        )

    def _build_fallback_response(
        self,
        *,
        user_message_content: str,
        snippets: list[str],
    ) -> str:
        """Build a deterministic answer when LLM generation is unavailable."""
        summary = "\n\n".join(snippets[:2]).strip()
        if not summary:
            return (
                "В документах текущего воркспейса не найдено достаточно "
                "контекста для ответа. Уточните вопрос или загрузите "
                "релевантные материалы."
            )

        return (
            "Не удалось обратиться к языковой модели, поэтому возвращаю "
            "краткий ответ по найденным фрагментам воркспейса.\n\n"
            f"Запрос: {user_message_content}\n\n"
            f"{summary}"
        )[:20_000]

    @staticmethod
    def _extract_message_content(payload: dict[str, Any]) -> str:
        """Extract text content from an OpenAI-compatible response payload."""
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise MessageGenerationError(
                "Unexpected LLM response payload",
            ) from exc

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(str(item))
            return "".join(parts)
        return str(content)
