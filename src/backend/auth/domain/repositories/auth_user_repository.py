"""Repository contract for authentication user access."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from auth.domain.entities.auth_user import AuthUser


class AuthUserRepository(ABC):
    """Provides user data for authentication."""

    @abstractmethod
    async def create(self, user: AuthUser) -> AuthUser:
        """Create a new user."""

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Return whether a user with email already exists."""

    @abstractmethod
    async def get_by_email(self, email: str) -> AuthUser | None:
        """Return a user by email."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> AuthUser | None:
        """Return a user by id."""
