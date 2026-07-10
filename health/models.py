"""Health check contracts and report models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, VersionInfo, utc_now


class HealthState(StrEnum):
    """Overall health state for a component or system."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ReadinessState(StrEnum):
    """Readiness probe state."""

    READY = "ready"
    NOT_READY = "not_ready"


class LivenessState(StrEnum):
    """Liveness probe state."""

    ALIVE = "alive"
    DEAD = "dead"


class DependencyStatus(PlatformModel):
    """Health status of an external dependency."""

    name: str = Field(min_length=1)
    state: HealthState
    message: str = Field(min_length=1)
    latency_ms: float | None = Field(default=None, ge=0)
    checked_at: UTCDateTime = Field(default_factory=utc_now)


class ComponentHealth(PlatformModel):
    """Health status of a registered component."""

    name: str = Field(min_length=1)
    state: HealthState
    message: str = Field(min_length=1)
    dependencies: tuple[DependencyStatus, ...] = Field(default_factory=tuple)
    checked_at: UTCDateTime = Field(default_factory=utc_now)


class SystemInformation(PlatformModel):
    """Runtime system information."""

    platform: str = Field(min_length=1)
    python_version: str = Field(min_length=1)
    hostname: str = Field(min_length=1)
    process_id: int = Field(ge=1)


class HealthReport(PlatformModel):
    """Aggregate health report for the platform."""

    readiness: ReadinessState
    liveness: LivenessState
    state: HealthState
    version: VersionInfo
    system: SystemInformation | None = None
    components: tuple[ComponentHealth, ...] = Field(default_factory=tuple)
    generated_at: UTCDateTime = Field(default_factory=utc_now)
