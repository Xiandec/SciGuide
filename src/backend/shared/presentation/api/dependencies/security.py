"""Mock security dependencies for presentation layer."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.presentation.api.mock_data import MOCK_USER_DISPLAY_NAME
from shared.presentation.api.mock_data import MOCK_USER_EMAIL
from shared.presentation.api.mock_data import MOCK_USER_ID

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class MockPrincipal:
    """Authenticated principal used by mock routes."""

    user_id: UUID
    email: str
    display_name: str
    token: str


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> MockPrincipal:
    """Return a stable mock principal for protected endpoints."""

    token = "mock-access-token"
    if credentials is not None:
        token = credentials.credentials

    return MockPrincipal(
        user_id=MOCK_USER_ID,
        email=MOCK_USER_EMAIL,
        display_name=MOCK_USER_DISPLAY_NAME,
        token=token,
    )
