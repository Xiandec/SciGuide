"""Security dependencies for presentation layer."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.application.use_cases.get_authenticated_user import (
    GetAuthenticatedUser,
)
from auth.application.use_cases.get_authenticated_user import (
    GetAuthenticatedUserRequest,
)
from auth.domain.exceptions.auth_exceptions import InactiveUserError
from auth.domain.exceptions.auth_exceptions import InvalidAccessTokenError
from auth.domain.exceptions.auth_exceptions import UnauthorizedError
from auth.domain.services.token_service import TokenService
from auth.presentation.api.dependencies import (
    get_authenticated_user_use_case,
)
from auth.presentation.api.dependencies import get_token_service

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Authenticated principal resolved from access token."""

    user_id: UUID
    email: str
    display_name: str
    token: str


MockPrincipal = AuthenticatedPrincipal


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    get_authenticated_user: GetAuthenticatedUser = Depends(
        get_authenticated_user_use_case,
    ),
    token_service: TokenService = Depends(get_token_service),
) -> AuthenticatedPrincipal:
    """Validate access token and resolve current user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required",
        )

    try:
        token_payload = token_service.decode_access_token(
            credentials.credentials,
        )
        user = await get_authenticated_user.execute(
            GetAuthenticatedUserRequest(user_id=token_payload.user_id),
        )
    except (
        InactiveUserError,
        InvalidAccessTokenError,
        UnauthorizedError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return AuthenticatedPrincipal(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        token=credentials.credentials,
    )
