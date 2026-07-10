"""Artifact health result contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel


class HealthStatus(StrEnum):
    """Health status for artifact management."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ArtifactHealthResult(PlatformModel):
    """Health check result for artifact management."""

    artifact_id: str
    status: HealthStatus
    message: str = ""
    details: dict[str, object] = Field(default_factory=dict)
