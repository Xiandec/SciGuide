"""Redis implementation of refresh token storage."""

from __future__ import annotations

from uuid import UUID

from redis.asyncio import Redis

from auth.domain.entities.refresh_token_session import RefreshTokenSession
from auth.domain.repositories.refresh_token_store import RefreshTokenStore


class RedisRefreshTokenStore(RefreshTokenStore):
    """Stores refresh tokens in Redis with TTL."""

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def save(
        self,
        session: RefreshTokenSession,
        ttl_seconds: int,
    ) -> None:
        """Store a refresh token session."""
        await self._redis.set(
            self._build_key(session.token_id),
            str(session.user_id),
            ex=ttl_seconds,
        )

    async def get_by_token_id(
        self,
        token_id: str,
    ) -> RefreshTokenSession | None:
        """Load refresh token session by token id."""
        user_id = await self._redis.get(self._build_key(token_id))
        if user_id is None:
            return None

        return RefreshTokenSession(
            token_id=token_id,
            user_id=UUID(str(user_id)),
        )

    async def delete(self, token_id: str) -> None:
        """Delete refresh token session by token id."""
        await self._redis.delete(self._build_key(token_id))

    @staticmethod
    def _build_key(token_id: str) -> str:
        """Build namespaced Redis key."""
        return f"auth:refresh:{token_id}"
