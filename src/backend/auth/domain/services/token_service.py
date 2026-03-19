"""Token service contracts and value objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from auth.domain.entities.auth_user import AuthUser


@dataclass(slots=True)
class AccessTokenPayload:
    """Decoded access token payload."""

    user_id: UUID
    email: str
    display_name: str


@dataclass(slots=True)
class GeneratedRefreshToken:
    """Generated refresh token pair."""

    token: str
    token_id: str


class TokenService(ABC):
    """Creates and validates auth tokens."""

    @abstractmethod
    def create_access_token(self, user: AuthUser) -> str:
        """Create a signed access token."""

    @abstractmethod
    def decode_access_token(self, token: str) -> AccessTokenPayload:
        """Decode and validate a signed access token."""

    @abstractmethod
    def generate_refresh_token(self) -> GeneratedRefreshToken:
        """Generate a new refresh token."""

    @abstractmethod
    def get_refresh_token_id(self, token: str) -> str:
        """Return a stable identifier for a refresh token."""
