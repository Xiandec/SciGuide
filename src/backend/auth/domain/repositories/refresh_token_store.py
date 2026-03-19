"""Repository contract for refresh token storage."""

from __future__ import annotations

from abc import ABC, abstractmethod

from auth.domain.entities.refresh_token_session import RefreshTokenSession


class RefreshTokenStore(ABC):
    """Stores refresh tokens outside the relational database."""

    @abstractmethod
    async def save(
        self,
        session: RefreshTokenSession,
        ttl_seconds: int,
    ) -> None:
        """Store a refresh token session."""

    @abstractmethod
    async def get_by_token_id(
        self,
        token_id: str,
    ) -> RefreshTokenSession | None:
        """Load a refresh token session."""

    @abstractmethod
    async def delete(self, token_id: str) -> None:
        """Delete a refresh token session."""
