"""Shared API dependencies."""

from shared.presentation.api.dependencies.security import (
    AuthenticatedPrincipal,
)
from shared.presentation.api.dependencies.security import MockPrincipal
from shared.presentation.api.dependencies.security import bearer_scheme
from shared.presentation.api.dependencies.security import get_current_principal

__all__ = [
    "AuthenticatedPrincipal",
    "MockPrincipal",
    "bearer_scheme",
    "get_current_principal",
]
