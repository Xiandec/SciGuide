"""Use case for user logout."""

from __future__ import annotations

from dataclasses import dataclass

from auth.domain.repositories.refresh_token_store import RefreshTokenStore
from auth.domain.services.token_service import TokenService


@dataclass(slots=True)
class LogoutUserRequest:
    """Logout request payload."""

    refresh_token: str


class LogoutUser:
    """Invalidate a refresh token."""

    def __init__(
        self,
        refresh_token_store: RefreshTokenStore,
        token_service: TokenService,
    ) -> None:
        self._refresh_token_store = refresh_token_store
        self._token_service = token_service

    async def execute(self, request: LogoutUserRequest) -> None:
        """Delete refresh token from the token store."""
        token_id = self._token_service.get_refresh_token_id(
            request.refresh_token,
        )
        await self._refresh_token_store.delete(token_id)
