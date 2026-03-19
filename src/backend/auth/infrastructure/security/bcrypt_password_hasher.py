"""BCrypt password hasher implementation."""

from __future__ import annotations

import bcrypt

from auth.domain.services.password_hasher import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """Hash and verify passwords with bcrypt."""

    def hash_password(self, password: str) -> str:
        """Return bcrypt hash for password."""
        password_bytes = password.encode("utf-8")
        password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        return password_hash.decode("utf-8")

    def verify_password(
        self,
        plain_password: str,
        password_hash: str,
    ) -> bool:
        """Verify password against bcrypt hash."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
