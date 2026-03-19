"""Mock authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from auth.presentation.api.schemas.auth_schemas import LoginRequest
from auth.presentation.api.schemas.auth_schemas import LoginResponse
from auth.presentation.api.schemas.auth_schemas import LogoutRequest
from auth.presentation.api.schemas.auth_schemas import RefreshTokenRequest
from auth.presentation.api.schemas.auth_schemas import RefreshTokenResponse
from auth.presentation.api.schemas.auth_schemas import UserSummaryResponse
from shared.presentation.api.dependencies.security import MockPrincipal
from shared.presentation.api.dependencies.security import get_current_principal
from shared.presentation.api.mock_data import MOCK_ACCESS_TOKEN
from shared.presentation.api.mock_data import MOCK_REFRESH_TOKEN
from shared.presentation.api.mock_data import build_user_summary

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Вход",
)
async def login(payload: LoginRequest) -> LoginResponse:
    """Return a mocked JWT pair and current user profile."""

    user_summary = build_user_summary()

    return LoginResponse(
        access_token=MOCK_ACCESS_TOKEN,
        refresh_token=MOCK_REFRESH_TOKEN,
        token_type="Bearer",
        expires_in=3600,
        user=UserSummaryResponse(
            id=user_summary["id"],
            email=user_summary["email"],
            display_name=user_summary["display_name"],
        ),
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление токена",
)
async def refresh(payload: RefreshTokenRequest) -> RefreshTokenResponse:
    """Return a stable mocked refresh response."""

    return RefreshTokenResponse(
        access_token=MOCK_ACCESS_TOKEN,
        refresh_token=payload.refresh_token or MOCK_REFRESH_TOKEN,
        token_type="Bearer",
        expires_in=3600,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Завершение сессии",
)
async def logout(payload: LogoutRequest) -> Response:
    """Acknowledge logout without body."""

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Текущий пользователь",
)
async def me(
    principal: MockPrincipal = Depends(get_current_principal),
) -> UserSummaryResponse:
    """Return the authenticated mock principal."""

    return UserSummaryResponse(
        id=principal.user_id,
        email=principal.email,
        display_name=principal.display_name,
    )
