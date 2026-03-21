"""Workspace member domain exceptions."""

from __future__ import annotations

from uuid import UUID


class WorkspaceMemberDomainError(Exception):
    """Base workspace member domain exception."""


class WorkspaceMemberNotFoundError(WorkspaceMemberDomainError):
    """Raised when a workspace member cannot be found."""

    def __init__(self, workspace_id: UUID, user_id: UUID) -> None:
        super().__init__(
            f"Workspace member {user_id} was not found in workspace "
            f"{workspace_id}",
        )


class WorkspaceMemberAlreadyExistsError(WorkspaceMemberDomainError):
    """Raised when trying to add an existing member again."""

    def __init__(self, workspace_id: UUID, user_id: UUID) -> None:
        super().__init__(
            f"User {user_id} is already a member of workspace "
            f"{workspace_id}",
        )


class WorkspaceMemberUserNotFoundError(WorkspaceMemberDomainError):
    """Raised when a target user does not exist."""

    def __init__(self, user_id: UUID) -> None:
        super().__init__(f"User {user_id} was not found")


class WorkspaceMemberOwnerImmutableError(WorkspaceMemberDomainError):
    """Raised when someone tries to modify the owner membership row."""

    def __init__(self) -> None:
        super().__init__("Workspace owner membership cannot be changed")


class WorkspaceMemberLastAdminError(WorkspaceMemberDomainError):
    """Raised when a mutation would leave the workspace without admins."""

    def __init__(self) -> None:
        super().__init__("Cannot remove or demote the last workspace admin")
