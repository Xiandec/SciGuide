"""Shared API schemas."""

from shared.presentation.api.schemas.common import CursorPage
from shared.presentation.api.schemas.common import DocumentContextItem
from shared.presentation.api.schemas.common import EmptyResponse
from shared.presentation.api.schemas.common import ErrorDetails
from shared.presentation.api.schemas.common import ErrorResponse
from shared.presentation.api.schemas.common import MessageContextResponse

__all__ = [
    "CursorPage",
    "DocumentContextItem",
    "EmptyResponse",
    "ErrorDetails",
    "ErrorResponse",
    "MessageContextResponse",
]
