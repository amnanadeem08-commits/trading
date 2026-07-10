"""Unit tests for monitoring scaffolds."""

from __future__ import annotations

import pytest

from config.settings import MonitoringSettings
from health.checks import CheckOutcome, CheckResult, StartupCheck
from models.common import VersionInfo
from monitoring import MonitoringService


class _StartupOk(StartupCheck):
    @property
    def name(self) -> str:
        return "config"

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, outcome=CheckOutcome.PASSED, message="ok")


@pytest.mark.unit
def test_monitoring_service_observable_contract() -> None:
    settings = MonitoringSettings(enabled=True, heartbeat_interval_seconds=60)
    service = MonitoringService(
        service_name="monitoring",
        version_info=VersionInfo(version_id="0.1.0"),
        settings=settings,
        startup_checks=(_StartupOk(),),
    )
    assert service.name() == "monitoring"
    assert service.version() == "0.1.0"
    startup = service.startup()
    assert startup[0].outcome == CheckOutcome.PASSED
    health = service.health()
    assert health.readiness.value == "ready"
    metrics = service.metrics()
    assert "counter:health_checks_total" in metrics
    assert "counter:startup_checks_total" in metrics


@pytest.mark.unit
def test_monitoring_service_shutdown_records_metrics() -> None:
    settings = MonitoringSettings(enabled=False)
    service = MonitoringService(
        service_name="monitoring",
        version_info=VersionInfo(version_id="0.1.0"),
        settings=settings,
    )
    service.shutdown()
    assert service.metrics()["counter:shutdown_checks_total"] == 0.0
