"""Workspaces persistence adapters."""

from .postgres_workspace_repository import (
    PostgresWorkspaceRepository,
)

__all__ = ["PostgresWorkspaceRepository"]
