"""Refresh token session entity."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class RefreshTokenSession:
    """Stored refresh token metadata."""

    token_id: str
    user_id: UUID

    def __post_init__(self) -> None:
        """Validate refresh token metadata."""
        self.token_id = self.token_id.strip()
        if not self.token_id:
            raise ValueError("Token id cannot be empty")
