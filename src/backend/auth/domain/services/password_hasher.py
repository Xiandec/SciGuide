"""Password hashing service contract."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Hashes and verifies user passwords."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a raw password."""

    @abstractmethod
    def verify_password(
        self,
        plain_password: str,
        password_hash: str,
    ) -> bool:
        """Verify a raw password against its hash."""
