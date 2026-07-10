"""Provider health result contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel


class HealthStatus(StrEnum):
    """Health status for a storage provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ProviderHealthResult(PlatformModel):
    """Result of a storage provider health check."""

    provider_id: str
    status: HealthStatus
    message: str = ""
    details: dict[str, object] = Field(default_factory=dict)
