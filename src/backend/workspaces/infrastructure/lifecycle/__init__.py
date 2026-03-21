"""Workspace lifecycle infrastructure adapters."""

from .http_workspace_lifecycle_manager import (
    HttpWorkspaceLifecycleManager,
)
from .noop_workspace_lifecycle_manager import (
    NoOpWorkspaceLifecycleManager,
)

__all__ = [
    "HttpWorkspaceLifecycleManager",
    "NoOpWorkspaceLifecycleManager",
]
