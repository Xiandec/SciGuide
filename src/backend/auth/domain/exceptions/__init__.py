"""Authentication domain exceptions."""

from auth.domain.exceptions.auth_exceptions import AuthDomainError
from auth.domain.exceptions.auth_exceptions import InactiveUserError
from auth.domain.exceptions.auth_exceptions import InvalidAccessTokenError
from auth.domain.exceptions.auth_exceptions import InvalidCredentialsError
from auth.domain.exceptions.auth_exceptions import InvalidRefreshTokenError
from auth.domain.exceptions.auth_exceptions import UnauthorizedError
from auth.domain.exceptions.auth_exceptions import UserAlreadyExistsError
from auth.domain.exceptions.auth_exceptions import WeakPasswordError

__all__ = [
    "AuthDomainError",
    "InactiveUserError",
    "InvalidAccessTokenError",
    "InvalidCredentialsError",
    "InvalidRefreshTokenError",
    "UnauthorizedError",
    "UserAlreadyExistsError",
    "WeakPasswordError",
]
