"""Workspace member domain exceptions."""

from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberAlreadyExistsError,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberDomainError,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberLastAdminError,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberNotFoundError,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberOwnerImmutableError,
)
from workspace_members.domain.exceptions.workspace_member_exceptions import (
    WorkspaceMemberUserNotFoundError,
)

__all__ = [
    "WorkspaceMemberAlreadyExistsError",
    "WorkspaceMemberDomainError",
    "WorkspaceMemberLastAdminError",
    "WorkspaceMemberNotFoundError",
    "WorkspaceMemberOwnerImmutableError",
    "WorkspaceMemberUserNotFoundError",
]
