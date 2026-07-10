"""Monitoring service scaffold."""

from __future__ import annotations

from typing import Any

from config.settings import MonitoringSettings
from health.checks import CheckResult, ShutdownCheck, StartupCheck
from health.models import HealthReport, HealthState
from health.observability import ObservableService
from metrics.registry import MetricRegistry
from models.common import VersionInfo
from monitoring.health import MonitoringHealthService


class MonitoringService(ObservableService):
    """Operational monitoring service without HTTP endpoints."""

    def __init__(
        self,
        *,
        service_name: str,
        version_info: VersionInfo,
        settings: MonitoringSettings,
        startup_checks: tuple[StartupCheck, ...] = (),
        shutdown_checks: tuple[ShutdownCheck, ...] = (),
    ) -> None:
        self._settings = settings
        self._metrics = MetricRegistry()
        self._health_service = MonitoringHealthService(
            service_name=service_name,
            version_info=version_info,
            settings=settings,
            metrics=self._metrics,
            startup_checks=startup_checks,
            shutdown_checks=shutdown_checks,
        )

    @property
    def health_service(self) -> MonitoringHealthService:
        return self._health_service

    @property
    def settings(self) -> MonitoringSettings:
        return self._settings

    def name(self) -> str:
        return self._health_service.name()

    def version(self) -> str:
        return self._health_service.version()

    def status(self) -> HealthState:
        return self._health_service.status()

    def health(self) -> HealthReport:
        return self._health_service.health()

    def metrics(self) -> dict[str, Any]:
        snapshot = self._metrics.snapshot()
        snapshot.update(self._health_service.metrics())
        return snapshot

    def startup(self) -> tuple[CheckResult, ...]:
        """Run startup checks and record metrics."""
        results = self._health_service.run_startup_checks()
        self._metrics.counter("startup_checks_total").inc(len(results))
        return results

    def shutdown(self) -> tuple[CheckResult, ...]:
        """Run shutdown checks and record metrics."""
        results = self._health_service.run_shutdown_checks()
        self._metrics.counter("shutdown_checks_total").inc(len(results))
        return results
