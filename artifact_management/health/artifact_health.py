"""Artifact health checker."""

from __future__ import annotations

from artifact_management.exceptions import ArtifactHealthError, ArtifactNotFoundError
from artifact_management.health.health_result import ArtifactHealthResult, HealthStatus
from artifact_management.registry.artifact_record import ArtifactState
from artifact_management.registry.artifact_registry import ArtifactRegistry


class ArtifactHealthChecker:
    """Performs metadata-only health checks for registered artifacts."""

    def __init__(self, *, registry: ArtifactRegistry) -> None:
        self._registry = registry

    def check(self, artifact_id: str) -> ArtifactHealthResult:
        try:
            record = self._registry.lookup(artifact_id)
        except ArtifactNotFoundError as error:
            raise ArtifactHealthError(str(error)) from error

        if record.state == ArtifactState.FAILED:
            return ArtifactHealthResult(
                artifact_id=artifact_id,
                status=HealthStatus.UNHEALTHY,
                message="artifact in failed state",
            )
        if record.state == ArtifactState.EXPIRED:
            return ArtifactHealthResult(
                artifact_id=artifact_id,
                status=HealthStatus.DEGRADED,
                message="artifact cache entry expired",
            )
        return ArtifactHealthResult(
            artifact_id=artifact_id,
            status=HealthStatus.HEALTHY,
            message=record.state.value,
            details={
                "artifact_id": artifact_id,
                "state": record.state.value,
                "uri": record.reference.uri,
            },
        )
