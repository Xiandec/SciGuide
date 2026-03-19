"""Shared DTOs for authentication use cases."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class AuthenticatedUserDTO:
    """Authenticated user summary."""

    id: UUID
    email: str
    display_name: str
