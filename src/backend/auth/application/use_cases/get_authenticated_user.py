"""Use case for loading the authenticated user."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from auth.application.dto.auth_dto import AuthenticatedUserDTO
from auth.domain.exceptions.auth_exceptions import UnauthorizedError
from auth.domain.repositories.auth_user_repository import AuthUserRepository


@dataclass(slots=True)
class GetAuthenticatedUserRequest:
    """Authenticated user request payload."""

    user_id: UUID


class GetAuthenticatedUser:
    """Load current authenticated user."""

    def __init__(self, user_repository: AuthUserRepository) -> None:
        self._user_repository = user_repository

    async def execute(
        self,
        request: GetAuthenticatedUserRequest,
    ) -> AuthenticatedUserDTO:
        """Resolve a current user from storage."""
        user = await self._user_repository.get_by_id(request.user_id)
        if user is None:
            raise UnauthorizedError()

        user.ensure_is_active()

        return AuthenticatedUserDTO(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
        )
