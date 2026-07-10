"""Unit tests for health scaffolds."""

from __future__ import annotations

import pytest

from health import (
    CheckOutcome,
    HealthRegistry,
    HealthService,
    HealthState,
    HeartbeatService,
    LivenessState,
    ReadinessState,
)
from health.checks import CheckResult, ShutdownCheck, StartupCheck
from models.common import ContractViolationError, VersionInfo


class _PassingStartupCheck(StartupCheck):
    @property
    def name(self) -> str:
        return "startup-ok"

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, outcome=CheckOutcome.PASSED, message="ok")


class _FailingShutdownCheck(ShutdownCheck):
    @property
    def name(self) -> str:
        return "shutdown-fail"

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, outcome=CheckOutcome.FAILED, message="fail")


@pytest.mark.unit
def test_health_registry_register_and_check() -> None:
    registry = HealthRegistry()

    def check() -> tuple[HealthState, str]:
        return HealthState.HEALTHY, "ok"

    registry.register("db", check)
    results = registry.check_all()
    assert len(results) == 1
    assert results[0].name == "db"
    assert results[0].state == HealthState.HEALTHY


@pytest.mark.unit
def test_health_registry_unregister_missing_raises() -> None:
    registry = HealthRegistry()
    with pytest.raises(ContractViolationError):
        registry.unregister("missing")


@pytest.mark.unit
def test_heartbeat_service_tracks_liveness() -> None:
    heartbeat = HeartbeatService(interval_seconds=3600)
    assert heartbeat.is_alive() is False
    heartbeat.beat()
    assert heartbeat.is_alive() is True
    assert heartbeat.status() == HealthState.HEALTHY


@pytest.mark.unit
def test_health_service_startup_shutdown_lifecycle() -> None:
    service = HealthService(
        service_name="platform",
        version_info=VersionInfo(version_id="1.0.0"),
        startup_checks=(_PassingStartupCheck(),),
        shutdown_checks=(_FailingShutdownCheck(),),
    )
    assert service.readiness() == ReadinessState.NOT_READY
    startup = service.run_startup_checks()
    assert startup[0].outcome == CheckOutcome.PASSED
    assert service.readiness() == ReadinessState.READY
    report = service.health()
    assert report.liveness == LivenessState.ALIVE
    assert report.state == HealthState.HEALTHY
    shutdown = service.run_shutdown_checks()
    assert shutdown[0].outcome == CheckOutcome.FAILED
    assert service.readiness() == ReadinessState.NOT_READY


@pytest.mark.unit
def test_health_service_observable_contract() -> None:
    service = HealthService(
        service_name="platform",
        version_info=VersionInfo(version_id="2.0.0"),
    )
    assert service.name() == "platform"
    assert service.version() == "2.0.0"
    assert "components_registered" in service.metrics()
