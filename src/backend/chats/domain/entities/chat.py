"""Chat domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Chat:
    """Personal chat bound to a single workspace and owner."""

    id: UUID
    workspace_id: UUID
    owner_user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None

    def __post_init__(self) -> None:
        """Normalize and validate chat state."""
        self.title = self.normalize_title(self.title)

        if (
            self.last_message_at is not None
            and self.last_message_at < self.created_at
        ):
            raise ValueError(
                "Chat last message timestamp cannot be earlier than creation",
            )

    @staticmethod
    def normalize_title(title: str) -> str:
        """Normalize and validate chat title."""
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("Chat title cannot be empty")

        return normalized_title
