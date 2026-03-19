"""Authentication API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from auth.application.use_cases.login_user import LoginUser
from auth.application.use_cases.login_user import LoginUserRequest
from auth.application.use_cases.logout_user import LogoutUser
from auth.application.use_cases.logout_user import LogoutUserRequest
from auth.application.use_cases.refresh_session import RefreshSession
from auth.application.use_cases.refresh_session import RefreshSessionRequest
from auth.domain.exceptions.auth_exceptions import InactiveUserError
from auth.domain.exceptions.auth_exceptions import InvalidCredentialsError
from auth.domain.exceptions.auth_exceptions import InvalidRefreshTokenError
from auth.presentation.api.dependencies import get_login_user_use_case
from auth.presentation.api.dependencies import get_logout_user_use_case
from auth.presentation.api.dependencies import get_refresh_session_use_case
from auth.presentation.api.schemas.auth_schemas import LoginRequest
from auth.presentation.api.schemas.auth_schemas import LoginResponse
from auth.presentation.api.schemas.auth_schemas import LogoutRequest
from auth.presentation.api.schemas.auth_schemas import RefreshTokenRequest
from auth.presentation.api.schemas.auth_schemas import RefreshTokenResponse
from auth.presentation.api.schemas.auth_schemas import UserSummaryResponse
from shared.presentation.api.dependencies.security import (
    AuthenticatedPrincipal,
)
from shared.presentation.api.dependencies.security import get_current_principal

router = APIRouter(prefix="/auth", tags=["Auth"])


def _raise_unauthorized(detail: str) -> None:
    """Raise a standard unauthorized HTTP error."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Вход",
)
async def login(
    payload: LoginRequest,
    use_case: LoginUser = Depends(get_login_user_use_case),
) -> LoginResponse:
    """Authenticate user and return token pair."""
    try:
        result = await use_case.execute(
            LoginUserRequest(
                email=payload.email,
                password=payload.password,
            ),
        )
    except (InactiveUserError, InvalidCredentialsError) as exc:
        _raise_unauthorized(str(exc))

    return LoginResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
        user=UserSummaryResponse(
            id=result.user.id,
            email=result.user.email,
            display_name=result.user.display_name,
        ),
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление токена",
)
async def refresh(
    payload: RefreshTokenRequest,
    use_case: RefreshSession = Depends(get_refresh_session_use_case),
) -> RefreshTokenResponse:
    """Rotate refresh token and return a new token pair."""
    try:
        result = await use_case.execute(
            RefreshSessionRequest(refresh_token=payload.refresh_token),
        )
    except (InactiveUserError, InvalidRefreshTokenError) as exc:
        _raise_unauthorized(str(exc))

    return RefreshTokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Завершение сессии",
)
async def logout(
    payload: LogoutRequest,
    use_case: LogoutUser = Depends(get_logout_user_use_case),
) -> Response:
    """Invalidate refresh token without response body."""
    try:
        await use_case.execute(
            LogoutUserRequest(refresh_token=payload.refresh_token),
        )
    except InvalidRefreshTokenError as exc:
        _raise_unauthorized(str(exc))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Текущий пользователь",
)
async def me(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> UserSummaryResponse:
    """Return authenticated principal summary."""
    return UserSummaryResponse(
        id=principal.user_id,
        email=principal.email,
        display_name=principal.display_name,
    )
