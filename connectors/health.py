"""Connector health contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class ConnectorHealthStatus(StrEnum):
    """Health status for connector connectivity."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    FAILED = "failed"


class HealthCheckResult(PlatformModel):
    """Result of a connector health check."""

    market_id: str = Field(min_length=1)
    status: ConnectorHealthStatus
    message: str = Field(min_length=1)
    latency_ms: float | None = Field(default=None, ge=0)
    checked_at: UTCDateTime = Field(default_factory=utc_now)
    details: dict[str, str | float | int | bool] = Field(default_factory=dict)
