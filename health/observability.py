"""Observable service contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from health.models import HealthReport, HealthState


class ObservableService(ABC):
    """Contract requiring version, status, health, metrics, and name."""

    @abstractmethod
    def name(self) -> str:
        """Return the service identifier."""

    @abstractmethod
    def version(self) -> str:
        """Return the service version string."""

    @abstractmethod
    def status(self) -> HealthState:
        """Return the current operational status."""

    @abstractmethod
    def health(self) -> HealthReport:
        """Return a full health report."""

    @abstractmethod
    def metrics(self) -> dict[str, Any]:
        """Return service metrics snapshot."""
