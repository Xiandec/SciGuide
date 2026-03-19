"""Authentication user entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from auth.domain.exceptions.auth_exceptions import InactiveUserError


@dataclass(slots=True)
class AuthUser:
    """User projection required for authentication flows."""

    id: UUID
    email: str
    display_name: str
    password_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Normalize and validate user state."""
        self.email = self.email.strip().lower()
        self.display_name = self.display_name.strip()
        self.password_hash = self.password_hash.strip()

        if not self.email:
            raise ValueError("Email cannot be empty")

        if not self.display_name:
            raise ValueError("Display name cannot be empty")

        if not self.password_hash:
            raise ValueError("Password hash cannot be empty")

    def ensure_is_active(self) -> None:
        """Raise when user is not allowed to authenticate."""
        if not self.is_active:
            raise InactiveUserError()
