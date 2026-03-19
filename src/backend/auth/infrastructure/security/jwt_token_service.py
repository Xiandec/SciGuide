"""JWT-based token service implementation."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt

from auth.domain.entities.auth_user import AuthUser
from auth.domain.exceptions.auth_exceptions import InvalidAccessTokenError
from auth.domain.exceptions.auth_exceptions import InvalidRefreshTokenError
from auth.domain.services.token_service import AccessTokenPayload
from auth.domain.services.token_service import GeneratedRefreshToken
from auth.domain.services.token_service import TokenService


class JwtTokenService(TokenService):
    """Issues JWT access tokens and opaque refresh tokens."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        access_token_expire_minutes: int,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes

    def create_access_token(self, user: AuthUser) -> str:
        """Create a signed access token."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(
            minutes=self._access_token_expire_minutes,
        )
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        return jwt.encode(
            payload,
            self._secret_key,
            algorithm=self._algorithm,
        )

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        """Decode and validate a signed access token."""
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except JWTError as exc:
            raise InvalidAccessTokenError() from exc

        if payload.get("type") != "access":
            raise InvalidAccessTokenError()

        user_id = payload.get("sub")
        email = payload.get("email")
        display_name = payload.get("display_name")
        if not user_id or not email or not display_name:
            raise InvalidAccessTokenError()

        try:
            parsed_user_id = UUID(user_id)
        except ValueError as exc:
            raise InvalidAccessTokenError() from exc

        return AccessTokenPayload(
            user_id=parsed_user_id,
            email=str(email),
            display_name=str(display_name),
        )

    def generate_refresh_token(self) -> GeneratedRefreshToken:
        """Generate a new opaque refresh token."""
        token = secrets.token_urlsafe(48)
        return GeneratedRefreshToken(
            token=token,
            token_id=self.get_refresh_token_id(token),
        )

    def get_refresh_token_id(self, token: str) -> str:
        """Hash refresh token into a stable storage identifier."""
        normalized_token = token.strip()
        if not normalized_token:
            raise InvalidRefreshTokenError()

        return hashlib.sha256(
            normalized_token.encode("utf-8"),
        ).hexdigest()
