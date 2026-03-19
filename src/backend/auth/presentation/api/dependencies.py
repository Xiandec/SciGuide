"""Dependency wiring for authentication."""

from __future__ import annotations

from functools import lru_cache

from asyncpg import Pool
from fastapi import Depends, Request
from redis.asyncio import Redis

from auth.application.use_cases.get_authenticated_user import (
    GetAuthenticatedUser,
)
from auth.application.use_cases.login_user import LoginUser
from auth.application.use_cases.logout_user import LogoutUser
from auth.application.use_cases.refresh_session import RefreshSession
from auth.domain.repositories.auth_user_repository import AuthUserRepository
from auth.domain.repositories.refresh_token_store import RefreshTokenStore
from auth.domain.services.password_hasher import PasswordHasher
from auth.domain.services.token_service import TokenService
from auth.infrastructure.persistence.postgres_auth_user_repository import (
    PostgresAuthUserRepository,
)
from auth.infrastructure.persistence.redis_refresh_token_store import (
    RedisRefreshTokenStore,
)
from auth.infrastructure.security.bcrypt_password_hasher import (
    BcryptPasswordHasher,
)
from auth.infrastructure.security.jwt_token_service import JwtTokenService
from config import settings


def get_db_pool(request: Request) -> Pool:
    """Return application PostgreSQL pool."""
    return request.app.state.db_pool


def get_redis_client(request: Request) -> Redis:
    """Return application Redis client."""
    return request.app.state.redis


def get_auth_user_repository(
    pool: Pool = Depends(get_db_pool),
) -> AuthUserRepository:
    """Build auth user repository."""
    return PostgresAuthUserRepository(pool)


def get_refresh_token_store(
    redis_client: Redis = Depends(get_redis_client),
) -> RefreshTokenStore:
    """Build refresh token store."""
    return RedisRefreshTokenStore(redis_client)


@lru_cache(maxsize=1)
def get_password_hasher() -> PasswordHasher:
    """Return password hasher singleton."""
    return BcryptPasswordHasher()


@lru_cache(maxsize=1)
def get_token_service() -> TokenService:
    """Return token service singleton."""
    return JwtTokenService(
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )


def get_login_user_use_case(
    user_repository: AuthUserRepository = Depends(get_auth_user_repository),
    refresh_token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: TokenService = Depends(get_token_service),
) -> LoginUser:
    """Build login use case."""
    return LoginUser(
        user_repository=user_repository,
        refresh_token_store=refresh_token_store,
        password_hasher=password_hasher,
        token_service=token_service,
        access_token_ttl_seconds=settings.access_token_expire_minutes * 60,
        refresh_token_ttl_seconds=settings.refresh_token_expire_days * 86400,
    )


def get_refresh_session_use_case(
    user_repository: AuthUserRepository = Depends(get_auth_user_repository),
    refresh_token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    token_service: TokenService = Depends(get_token_service),
) -> RefreshSession:
    """Build refresh use case."""
    return RefreshSession(
        user_repository=user_repository,
        refresh_token_store=refresh_token_store,
        token_service=token_service,
        access_token_ttl_seconds=settings.access_token_expire_minutes * 60,
        refresh_token_ttl_seconds=settings.refresh_token_expire_days * 86400,
    )


def get_logout_user_use_case(
    refresh_token_store: RefreshTokenStore = Depends(get_refresh_token_store),
    token_service: TokenService = Depends(get_token_service),
) -> LogoutUser:
    """Build logout use case."""
    return LogoutUser(
        refresh_token_store=refresh_token_store,
        token_service=token_service,
    )


def get_authenticated_user_use_case(
    user_repository: AuthUserRepository = Depends(get_auth_user_repository),
) -> GetAuthenticatedUser:
    """Build current user use case."""
    return GetAuthenticatedUser(user_repository=user_repository)
