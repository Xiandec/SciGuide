"""Use case for user login."""

from __future__ import annotations

from dataclasses import dataclass

from auth.application.dto.auth_dto import AuthenticatedUserDTO
from auth.domain.entities.refresh_token_session import RefreshTokenSession
from auth.domain.exceptions.auth_exceptions import InvalidCredentialsError
from auth.domain.repositories.auth_user_repository import AuthUserRepository
from auth.domain.repositories.refresh_token_store import RefreshTokenStore
from auth.domain.services.password_hasher import PasswordHasher
from auth.domain.services.token_service import TokenService


@dataclass(slots=True)
class LoginUserRequest:
    """Login request payload."""

    email: str
    password: str


@dataclass(slots=True)
class LoginUserResponse:
    """Login response payload."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: AuthenticatedUserDTO


class LoginUser:
    """Authenticate a user and create a token pair."""

    def __init__(
        self,
        user_repository: AuthUserRepository,
        refresh_token_store: RefreshTokenStore,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        access_token_ttl_seconds: int,
        refresh_token_ttl_seconds: int,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_store = refresh_token_store
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._access_token_ttl_seconds = access_token_ttl_seconds
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds

    async def execute(
        self,
        request: LoginUserRequest,
    ) -> LoginUserResponse:
        """Authenticate user credentials."""
        user = await self._user_repository.get_by_email(request.email)
        if user is None:
            raise InvalidCredentialsError()

        user.ensure_is_active()

        is_valid = self._password_hasher.verify_password(
            request.password,
            user.password_hash,
        )
        if not is_valid:
            raise InvalidCredentialsError()

        access_token = self._token_service.create_access_token(user)
        refresh_token = self._token_service.generate_refresh_token()

        await self._refresh_token_store.save(
            RefreshTokenSession(
                token_id=refresh_token.token_id,
                user_id=user.id,
            ),
            ttl_seconds=self._refresh_token_ttl_seconds,
        )

        return LoginUserResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            token_type="Bearer",
            expires_in=self._access_token_ttl_seconds,
            user=AuthenticatedUserDTO(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
            ),
        )
