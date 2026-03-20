"""Use case for user registration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from auth.application.dto.auth_dto import AuthenticatedUserDTO
from auth.domain.entities.auth_user import AuthUser
from auth.domain.entities.refresh_token_session import RefreshTokenSession
from auth.domain.exceptions.auth_exceptions import UserAlreadyExistsError
from auth.domain.exceptions.auth_exceptions import WeakPasswordError
from auth.domain.repositories.auth_user_repository import AuthUserRepository
from auth.domain.repositories.refresh_token_store import RefreshTokenStore
from auth.domain.services.password_hasher import PasswordHasher
from auth.domain.services.token_service import TokenService


@dataclass(slots=True)
class RegisterUserRequest:
    """Registration request payload."""

    email: str
    display_name: str
    password: str


@dataclass(slots=True)
class RegisterUserResponse:
    """Registration response payload."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: AuthenticatedUserDTO


class RegisterUser:
    """Register a new user and create an auth session."""

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
        request: RegisterUserRequest,
    ) -> RegisterUserResponse:
        """Create user account and issue tokens."""
        if len(request.password) < 8:
            raise WeakPasswordError()

        if await self._user_repository.exists_by_email(request.email):
            raise UserAlreadyExistsError(request.email)

        now = datetime.now(timezone.utc)
        user = AuthUser(
            id=uuid4(),
            email=request.email,
            display_name=request.display_name,
            password_hash=self._password_hasher.hash_password(
                request.password,
            ),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        created_user = await self._user_repository.create(user)

        access_token = self._token_service.create_access_token(created_user)
        refresh_token = self._token_service.generate_refresh_token()

        await self._refresh_token_store.save(
            RefreshTokenSession(
                token_id=refresh_token.token_id,
                user_id=created_user.id,
            ),
            ttl_seconds=self._refresh_token_ttl_seconds,
        )

        return RegisterUserResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            token_type="Bearer",
            expires_in=self._access_token_ttl_seconds,
            user=AuthenticatedUserDTO(
                id=created_user.id,
                email=created_user.email,
                display_name=created_user.display_name,
            ),
        )
