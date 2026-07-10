"""Plugin health result contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel


class PluginHealthStatus(StrEnum):
    """Health status for ML engine plugins."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class PluginHealthResult(PlatformModel):
    """Health check result for a plugin."""

    plugin_id: str
    status: PluginHealthStatus
    message: str = ""
    details: dict[str, object] = Field(default_factory=dict)
