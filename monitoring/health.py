"""Monitoring health orchestration."""

from __future__ import annotations

from config.settings import MonitoringSettings
from health.checks import ShutdownCheck, StartupCheck
from health.heartbeat import HeartbeatService
from health.models import HealthReport
from health.registry import HealthRegistry
from health.service import HealthService
from metrics.registry import MetricRegistry
from models.common import VersionInfo


class MonitoringHealthService(HealthService):
    """Health service configured from monitoring settings."""

    def __init__(
        self,
        *,
        service_name: str,
        version_info: VersionInfo,
        settings: MonitoringSettings,
        registry: HealthRegistry | None = None,
        metrics: MetricRegistry | None = None,
        startup_checks: tuple[StartupCheck, ...] = (),
        shutdown_checks: tuple[ShutdownCheck, ...] = (),
    ) -> None:
        heartbeat = (
            HeartbeatService(settings.heartbeat_interval_seconds) if settings.enabled else None
        )
        super().__init__(
            service_name=service_name,
            version_info=version_info,
            registry=registry,
            heartbeat=heartbeat,
            startup_checks=startup_checks,
            shutdown_checks=shutdown_checks,
            collect_system_info=settings.collect_system_info,
        )
        self._metrics = metrics or MetricRegistry()
        if settings.enabled:
            self._metrics.gauge("monitoring_enabled").set(1.0)

    @property
    def metrics_registry(self) -> MetricRegistry:
        return self._metrics

    def health(self) -> HealthReport:
        report = super().health()
        self._metrics.counter("health_checks_total").inc()
        return report
