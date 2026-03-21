"""Messages persistence adapters."""

from messages.infrastructure.persistence.postgres_message_repository import (
    PostgresMessageRepository,
)

__all__ = ["PostgresMessageRepository"]
