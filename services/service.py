"""Base service contract for the platform service layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from health.models import HealthReport, HealthState


class ServiceState(StrEnum):
    """Operational state tracked by the service layer."""

    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class BaseService(ABC):
    """Contract implemented by every platform service."""

    @abstractmethod
    def name(self) -> str:
        """Return the unique service identifier."""

    @abstractmethod
    def version(self) -> str:
        """Return the service version string."""

    @abstractmethod
    def start(self) -> None:
        """Start the service."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the service."""

    @abstractmethod
    def health(self) -> HealthReport:
        """Return a full health report."""

    @abstractmethod
    def status(self) -> HealthState:
        """Return the current operational status."""

    @abstractmethod
    def metrics(self) -> dict[str, Any]:
        """Return service metrics snapshot."""

    @abstractmethod
    def dependencies(self) -> tuple[str, ...]:
        """Return service names this service depends on."""

    @abstractmethod
    def ready(self) -> bool:
        """Return whether the service is ready to serve work."""
