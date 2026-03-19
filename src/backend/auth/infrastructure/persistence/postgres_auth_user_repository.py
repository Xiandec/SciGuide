"""PostgreSQL implementation of auth user repository."""

from __future__ import annotations

from uuid import UUID

from asyncpg import Pool, Record

from auth.domain.entities.auth_user import AuthUser
from auth.domain.repositories.auth_user_repository import AuthUserRepository


class PostgresAuthUserRepository(AuthUserRepository):
    """Loads authentication users from PostgreSQL."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def get_by_email(self, email: str) -> AuthUser | None:
        """Return a user by normalized email."""
        record = await self._pool.fetchrow(
            """
            SELECT
                id,
                email,
                display_name,
                password_hash,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE lower(email) = lower($1)
            """,
            email.strip(),
        )
        return self._build_user(record)

    async def get_by_id(self, user_id: UUID) -> AuthUser | None:
        """Return a user by id."""
        record = await self._pool.fetchrow(
            """
            SELECT
                id,
                email,
                display_name,
                password_hash,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE id = $1
            """,
            user_id,
        )
        return self._build_user(record)

    @staticmethod
    def _build_user(record: Record | None) -> AuthUser | None:
        """Convert a PostgreSQL row into a domain entity."""
        if record is None:
            return None

        return AuthUser(
            id=record["id"],
            email=record["email"],
            display_name=record["display_name"],
            password_hash=record["password_hash"],
            is_active=record["is_active"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )
