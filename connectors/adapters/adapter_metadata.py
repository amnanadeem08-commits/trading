"""Adapter metadata contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel


class AdapterState(StrEnum):
    """Lifecycle states for execution adapters."""

    REGISTERED = "registered"
    INITIALIZED = "initialized"
    VALIDATED = "validated"
    ACTIVE = "active"
    SHUTDOWN = "shutdown"
    FAILED = "failed"


TERMINAL_ADAPTER_STATES: frozenset[AdapterState] = frozenset(
    {
        AdapterState.SHUTDOWN,
        AdapterState.FAILED,
    },
)


class AdapterHealthStatus(StrEnum):
    """Health status for an execution adapter."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class AdapterHealthResult(PlatformModel):
    """Outcome of an adapter health check."""

    adapter_id: str = Field(min_length=1)
    status: AdapterHealthStatus = AdapterHealthStatus.HEALTHY
    message: str = ""


class AdapterMetadata(PlatformModel):
    """Metadata for a registered execution adapter."""

    adapter_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
