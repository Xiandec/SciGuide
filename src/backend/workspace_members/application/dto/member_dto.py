"""Workspace member DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from workspaces.domain.entities.workspace import WorkspaceRole
from workspace_members.domain.entities.workspace_member import (
    WorkspaceMember,
)


@dataclass(slots=True)
class WorkspaceMemberDTO:
    """Workspace member payload returned to presentation."""

    user_id: UUID
    email: str | None
    display_name: str | None
    role: WorkspaceRole
    joined_at: datetime

    @classmethod
    def from_entity(cls, member: WorkspaceMember) -> "WorkspaceMemberDTO":
        """Build DTO from a member projection."""
        return cls(
            user_id=member.user_id,
            email=member.email,
            display_name=member.display_name,
            role=member.role,
            joined_at=member.joined_at,
        )


@dataclass(slots=True)
class WorkspaceMemberListDTO:
    """Workspace member collection payload."""

    items: list[WorkspaceMemberDTO]
