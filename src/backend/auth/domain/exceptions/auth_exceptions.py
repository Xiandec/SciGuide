"""Authentication domain exceptions."""


class AuthDomainError(Exception):
    """Base authentication error."""


class InvalidCredentialsError(AuthDomainError):
    """Raised when email or password is invalid."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InactiveUserError(AuthDomainError):
    """Raised when user is disabled."""

    def __init__(self) -> None:
        super().__init__("User account is inactive")


class InvalidAccessTokenError(AuthDomainError):
    """Raised when access token is invalid."""

    def __init__(self) -> None:
        super().__init__("Access token is invalid or expired")


class InvalidRefreshTokenError(AuthDomainError):
    """Raised when refresh token is invalid."""

    def __init__(self) -> None:
        super().__init__("Refresh token is invalid or expired")


class UnauthorizedError(AuthDomainError):
    """Raised when principal cannot be resolved."""

    def __init__(self) -> None:
        super().__init__("Authentication is required")


class UserAlreadyExistsError(AuthDomainError):
    """Raised when user email is already registered."""

    def __init__(self, email: str) -> None:
        super().__init__(f"User with email {email} already exists")


class WeakPasswordError(AuthDomainError):
    """Raised when password does not satisfy policy."""

    def __init__(self) -> None:
        super().__init__("Password must contain at least 8 characters")
