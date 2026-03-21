"""Celery application configuration."""

from __future__ import annotations

from urllib.parse import quote

from celery import Celery

from config import settings


def _build_redis_url() -> str:
    """Build Redis URL from application settings."""
    password = settings.redis_password
    auth_part = f":{quote(password)}@" if password else ""
    return (
        f"redis://{auth_part}{settings.redis_host}:"
        f"{settings.redis_port}/{settings.redis_db}"
    )


celery_app = Celery(
    "sciguide",
    broker=_build_redis_url(),
    backend=_build_redis_url(),
    include=["workspace_documents.infrastructure.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_default_queue="workspace-document-indexing",
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
)

__all__ = ["celery_app"]
