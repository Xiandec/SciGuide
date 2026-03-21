"""Workspace domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class WorkspaceType(str, Enum):
    """Supported workspace types."""

    PRIVATE = "private"
    SHARED = "shared"


class WorkspaceAccessMode(str, Enum):
    """Supported workspace access modes."""

    OWNER_ONLY = "owner_only"
    BY_MEMBERSHIP = "by_membership"
    GLOBAL = "global"


class WorkspaceRole(str, Enum):
    """User roles inside a workspace."""

    ADMIN = "admin"
    USER = "user"


@dataclass(slots=True)
class Workspace:
    """Workspace aggregate stored in PostgreSQL."""

    id: UUID
    owner_user_id: UUID
    name: str
    description: str | None
    type: WorkspaceType
    access_mode: WorkspaceAccessMode
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Normalize and validate workspace state."""
        self.name = self.name.strip()
        if self.description is not None:
            self.description = self.description.strip() or None

        if not self.name:
            raise ValueError("Workspace name cannot be empty")

        if self.type == WorkspaceType.PRIVATE:
            if self.access_mode != WorkspaceAccessMode.OWNER_ONLY:
                raise ValueError(
                    "Private workspace must use owner_only access mode",
                )
            return

        if self.access_mode == WorkspaceAccessMode.OWNER_ONLY:
            raise ValueError(
                "Shared workspace cannot use owner_only access mode",
            )


@dataclass(slots=True)
class WorkspaceAccess:
    """Workspace view enriched with the caller role."""

    workspace: Workspace
    my_role: WorkspaceRole
