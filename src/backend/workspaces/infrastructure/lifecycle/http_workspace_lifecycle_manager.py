"""HTTP-based workspace lifecycle manager for Qdrant and Neo4j."""

from __future__ import annotations

from datetime import timezone

import httpx

from workspaces.domain.entities.workspace import Workspace
from workspaces.domain.exceptions.workspace_exceptions import (
    WorkspaceLifecycleError,
)
from workspaces.domain.services.workspace_lifecycle_manager import (
    WorkspaceLifecycleManager,
)


class HttpWorkspaceLifecycleManager(WorkspaceLifecycleManager):
    """Provision workspace resources in Qdrant and Neo4j over HTTP."""

    def __init__(
        self,
        *,
        qdrant_url: str,
        qdrant_collection_prefix: str,
        qdrant_vector_size: int,
        qdrant_distance: str,
        neo4j_url: str,
        neo4j_username: str,
        neo4j_password: str,
        neo4j_database: str,
        neo4j_root_label: str,
        timeout_seconds: float,
    ) -> None:
        self._qdrant_url = qdrant_url.rstrip("/")
        self._qdrant_collection_prefix = qdrant_collection_prefix
        self._qdrant_vector_size = qdrant_vector_size
        self._qdrant_distance = qdrant_distance
        self._neo4j_url = neo4j_url.rstrip("/")
        self._neo4j_username = neo4j_username
        self._neo4j_password = neo4j_password
        self._neo4j_database = neo4j_database
        self._neo4j_root_label = neo4j_root_label
        self._timeout_seconds = timeout_seconds

    async def provision(self, workspace: Workspace) -> None:
        """Create isolated storage resources for a workspace."""
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
            ) as client:
                await self._create_qdrant_collection(client, workspace)
                await self._create_neo4j_structure(client, workspace)
        except httpx.HTTPError as exc:
            raise WorkspaceLifecycleError(
                "Failed to provision external resources "
                f"for workspace {workspace.id}",
            ) from exc

    async def teardown(self, workspace: Workspace) -> None:
        """Delete isolated storage resources for a workspace."""
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
            ) as client:
                await self._delete_qdrant_collection(client, workspace)
                await self._delete_neo4j_structure(client, workspace)
        except httpx.HTTPError as exc:
            raise WorkspaceLifecycleError(
                "Failed to remove external resources "
                f"for workspace {workspace.id}",
            ) from exc

    async def _create_qdrant_collection(
        self,
        client: httpx.AsyncClient,
        workspace: Workspace,
    ) -> None:
        """Provision Qdrant collection for a workspace."""
        response = await client.put(
            self._qdrant_collection_url(workspace),
            json={
                "vectors": {
                    "size": self._qdrant_vector_size,
                    "distance": self._qdrant_distance,
                },
            },
        )
        response.raise_for_status()

    async def _delete_qdrant_collection(
        self,
        client: httpx.AsyncClient,
        workspace: Workspace,
    ) -> None:
        """Delete Qdrant collection for a workspace."""
        response = await client.delete(self._qdrant_collection_url(workspace))
        if response.status_code == httpx.codes.NOT_FOUND:
            return
        response.raise_for_status()

    async def _create_neo4j_structure(
        self,
        client: httpx.AsyncClient,
        workspace: Workspace,
    ) -> None:
        """Create root graph node that scopes workspace graph data."""
        response = await client.post(
            self._neo4j_commit_url(),
            auth=(self._neo4j_username, self._neo4j_password),
            json={
                "statements": [
                    {
                        "statement": (
                            f"MERGE (root:{self._neo4j_root_label} "
                            "{workspace_id: $workspace_id}) "
                            "ON CREATE SET "
                            "root.created_at = datetime($created_at), "
                            "root.workspace_name = $workspace_name "
                            "SET root.updated_at = datetime($updated_at), "
                            "root.workspace_type = $workspace_type"
                        ),
                        "parameters": {
                            "workspace_id": str(workspace.id),
                            "workspace_name": workspace.name,
                            "workspace_type": workspace.type.value,
                            "created_at": workspace.created_at.astimezone(
                                timezone.utc,
                            ).isoformat(),
                            "updated_at": workspace.updated_at.astimezone(
                                timezone.utc,
                            ).isoformat(),
                        },
                    },
                ],
            },
        )
        response.raise_for_status()
        self._raise_on_neo4j_errors(response)

    async def _delete_neo4j_structure(
        self,
        client: httpx.AsyncClient,
        workspace: Workspace,
    ) -> None:
        """Delete all graph nodes that belong to a workspace."""
        response = await client.post(
            self._neo4j_commit_url(),
            auth=(self._neo4j_username, self._neo4j_password),
            json={
                "statements": [
                    {
                        "statement": (
                            "MATCH (n {workspace_id: $workspace_id}) "
                            "DETACH DELETE n"
                        ),
                        "parameters": {
                            "workspace_id": str(workspace.id),
                        },
                    },
                ],
            },
        )
        response.raise_for_status()
        self._raise_on_neo4j_errors(response)

    def _qdrant_collection_url(self, workspace: Workspace) -> str:
        """Return Qdrant collection URL for a workspace."""
        collection_name = f"{self._qdrant_collection_prefix}{workspace.id.hex}"
        return f"{self._qdrant_url}/collections/{collection_name}"

    def _neo4j_commit_url(self) -> str:
        """Return Neo4j transaction commit endpoint."""
        return f"{self._neo4j_url}/db/{self._neo4j_database}/tx/commit"

    @staticmethod
    def _raise_on_neo4j_errors(response: httpx.Response) -> None:
        """Translate Neo4j transactional errors into domain errors."""
        payload = response.json()
        errors = payload.get("errors", [])
        if not errors:
            return

        messages = ", ".join(
            error.get("message", "unknown error")
            for error in errors
        )
        raise WorkspaceLifecycleError(messages)
