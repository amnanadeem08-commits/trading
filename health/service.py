"""Health service combining registry, checks, and reporting."""

from __future__ import annotations

import os
import platform
import sys
from typing import Any

from health.checks import CheckResult, ShutdownCheck, StartupCheck
from health.heartbeat import HeartbeatService
from health.models import (
    ComponentHealth,
    HealthReport,
    HealthState,
    LivenessState,
    ReadinessState,
    SystemInformation,
)
from health.observability import ObservableService
from health.registry import HealthRegistry
from models.common import VersionInfo, utc_now


class HealthService(ObservableService):
    """Reusable health service without HTTP endpoints."""

    def __init__(
        self,
        *,
        service_name: str,
        version_info: VersionInfo,
        registry: HealthRegistry | None = None,
        heartbeat: HeartbeatService | None = None,
        startup_checks: tuple[StartupCheck, ...] = (),
        shutdown_checks: tuple[ShutdownCheck, ...] = (),
        collect_system_info: bool = True,
    ) -> None:
        self._service_name = service_name
        self._version_info = version_info
        self._registry = registry or HealthRegistry()
        self._heartbeat = heartbeat
        self._startup_checks = startup_checks
        self._shutdown_checks = shutdown_checks
        self._collect_system_info = collect_system_info
        self._startup_results: tuple[CheckResult, ...] = ()
        self._shutdown_results: tuple[CheckResult, ...] = ()
        self._ready = False

    @property
    def registry(self) -> HealthRegistry:
        return self._registry

    def name(self) -> str:
        return self._service_name

    def version(self) -> str:
        return self._version_info.version_id

    def status(self) -> HealthState:
        return self.health().state

    def metrics(self) -> dict[str, Any]:
        return {
            "components_registered": len(self._registry.list_components()),
            "ready": self._ready,
            "startup_checks": len(self._startup_results),
            "shutdown_checks": len(self._shutdown_results),
        }

    def run_startup_checks(self) -> tuple[CheckResult, ...]:
        """Execute all startup checks."""
        results = [check.run() for check in self._startup_checks]
        self._startup_results = tuple(results)
        self._ready = all(result.outcome.value == "passed" for result in results)
        return self._startup_results

    def run_shutdown_checks(self) -> tuple[CheckResult, ...]:
        """Execute all shutdown checks."""
        results = [check.run() for check in self._shutdown_checks]
        self._shutdown_results = tuple(results)
        self._ready = False
        return self._shutdown_results

    def readiness(self) -> ReadinessState:
        return ReadinessState.READY if self._ready else ReadinessState.NOT_READY

    def liveness(self) -> LivenessState:
        if self._heartbeat is None:
            return LivenessState.ALIVE
        return LivenessState.ALIVE if self._heartbeat.is_alive() else LivenessState.DEAD

    def system_information(self) -> SystemInformation | None:
        if not self._collect_system_info:
            return None
        return SystemInformation(
            platform=platform.platform(),
            python_version=sys.version.split()[0],
            hostname=platform.node(),
            process_id=os.getpid(),
        )

    def health(self) -> HealthReport:
        components = self._registry.check_all()
        state = self._aggregate_state(components)
        return HealthReport(
            readiness=self.readiness(),
            liveness=self.liveness(),
            state=state,
            version=self._version_info,
            system=self.system_information(),
            components=components,
            generated_at=utc_now(),
        )

    def _aggregate_state(self, components: tuple[ComponentHealth, ...]) -> HealthState:
        if not components:
            return HealthState.HEALTHY
        states = {component.state for component in components}
        if HealthState.UNHEALTHY in states:
            return HealthState.UNHEALTHY
        if HealthState.DEGRADED in states:
            return HealthState.DEGRADED
        if HealthState.UNKNOWN in states:
            return HealthState.UNKNOWN
        return HealthState.HEALTHY
