"""Use case for access token refresh."""

from __future__ import annotations

from dataclasses import dataclass

from auth.domain.entities.refresh_token_session import RefreshTokenSession
from auth.domain.exceptions.auth_exceptions import InvalidRefreshTokenError
from auth.domain.repositories.auth_user_repository import AuthUserRepository
from auth.domain.repositories.refresh_token_store import RefreshTokenStore
from auth.domain.services.token_service import TokenService


@dataclass(slots=True)
class RefreshSessionRequest:
    """Refresh request payload."""

    refresh_token: str


@dataclass(slots=True)
class RefreshSessionResponse:
    """Refresh response payload."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshSession:
    """Rotate refresh token and create a new access token."""

    def __init__(
        self,
        user_repository: AuthUserRepository,
        refresh_token_store: RefreshTokenStore,
        token_service: TokenService,
        access_token_ttl_seconds: int,
        refresh_token_ttl_seconds: int,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_store = refresh_token_store
        self._token_service = token_service
        self._access_token_ttl_seconds = access_token_ttl_seconds
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds

    async def execute(
        self,
        request: RefreshSessionRequest,
    ) -> RefreshSessionResponse:
        """Refresh token pair using a valid refresh token."""
        current_token_id = self._token_service.get_refresh_token_id(
            request.refresh_token,
        )
        session = await self._refresh_token_store.get_by_token_id(
            current_token_id,
        )
        if session is None:
            raise InvalidRefreshTokenError()

        user = await self._user_repository.get_by_id(session.user_id)
        if user is None:
            await self._refresh_token_store.delete(current_token_id)
            raise InvalidRefreshTokenError()

        user.ensure_is_active()

        await self._refresh_token_store.delete(current_token_id)

        access_token = self._token_service.create_access_token(user)
        refresh_token = self._token_service.generate_refresh_token()

        await self._refresh_token_store.save(
            RefreshTokenSession(
                token_id=refresh_token.token_id,
                user_id=user.id,
            ),
            ttl_seconds=self._refresh_token_ttl_seconds,
        )

        return RefreshSessionResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            token_type="Bearer",
            expires_in=self._access_token_ttl_seconds,
        )
