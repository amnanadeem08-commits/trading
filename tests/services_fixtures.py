"""Test service implementations for the service layer."""

from __future__ import annotations

import os
import platform
import sys
from typing import Any

from health.models import (
    ComponentHealth,
    HealthReport,
    HealthState,
    LivenessState,
    ReadinessState,
    SystemInformation,
)
from models.common import VersionInfo, utc_now
from services.decorators import service
from services.service import BaseService, ServiceState


class _ServiceStateTracker:
    def __init__(self) -> None:
        self.state = ServiceState.REGISTERED
        self.started = False
        self.stopped = False
        self.fail_start = False
        self.fail_stop = False
        self.ready = False


@service(name="alpha", auto_register=False)
class AlphaService(BaseService):
    """Primary test service with no dependencies."""

    def __init__(self) -> None:
        self._tracker = _ServiceStateTracker()
        self._version = "1.0.0"

    def name(self) -> str:
        return "alpha"

    def version(self) -> str:
        return self._version

    def start(self) -> None:
        if self._tracker.fail_start:
            msg = "alpha start failed"
            raise RuntimeError(msg)
        self._tracker.started = True
        self._tracker.state = ServiceState.RUNNING
        self._tracker.ready = True

    def stop(self) -> None:
        if self._tracker.fail_stop:
            msg = "alpha stop failed"
            raise RuntimeError(msg)
        self._tracker.stopped = True
        self._tracker.state = ServiceState.STOPPED
        self._tracker.ready = False

    def health(self) -> HealthReport:
        return HealthReport(
            readiness=ReadinessState.READY if self.ready() else ReadinessState.NOT_READY,
            liveness=LivenessState.ALIVE,
            state=self.status(),
            version=VersionInfo(version_id=self.version()),
            system=SystemInformation(
                platform=platform.platform(),
                python_version=sys.version.split()[0],
                hostname=platform.node(),
                process_id=os.getpid(),
            ),
            components=(
                ComponentHealth(
                    name=self.name(),
                    state=self.status(),
                    message="ok",
                ),
            ),
            generated_at=utc_now(),
        )

    def status(self) -> HealthState:
        if self._tracker.state == ServiceState.FAILED:
            return HealthState.UNHEALTHY
        if self._tracker.ready:
            return HealthState.HEALTHY
        return HealthState.DEGRADED

    def metrics(self) -> dict[str, Any]:
        return {
            "started": self._tracker.started,
            "stopped": self._tracker.stopped,
            "ready": self._tracker.ready,
        }

    def dependencies(self) -> tuple[str, ...]:
        return ()

    def ready(self) -> bool:
        return self._tracker.ready


@service(name="beta", auto_register=False)
class BetaService(BaseService):
    """Dependent test service."""

    def __init__(self, alpha: AlphaService) -> None:
        self._alpha = alpha
        self._ready = False

    def name(self) -> str:
        return "beta"

    def version(self) -> str:
        return "1.0.0"

    def start(self) -> None:
        if not self._alpha.ready():
            msg = "alpha not ready"
            raise RuntimeError(msg)
        self._ready = True

    def stop(self) -> None:
        self._ready = False

    def health(self) -> HealthReport:
        return HealthReport(
            readiness=ReadinessState.READY if self.ready() else ReadinessState.NOT_READY,
            liveness=LivenessState.ALIVE,
            state=HealthState.HEALTHY if self.ready() else HealthState.DEGRADED,
            version=VersionInfo(version_id=self.version()),
            generated_at=utc_now(),
        )

    def status(self) -> HealthState:
        return HealthState.HEALTHY if self.ready() else HealthState.DEGRADED

    def metrics(self) -> dict[str, Any]:
        return {"ready": self._ready}

    def dependencies(self) -> tuple[str, ...]:
        return ("alpha",)

    def ready(self) -> bool:
        return self._ready


@service(name="gamma", auto_register=True)
class GammaService(BaseService):
    """Auto-discoverable test service."""

    def __init__(self) -> None:
        self._ready = False

    def name(self) -> str:
        return "gamma"

    def version(self) -> str:
        return "0.1.0"

    def start(self) -> None:
        self._ready = True

    def stop(self) -> None:
        self._ready = False

    def health(self) -> HealthReport:
        return HealthReport(
            readiness=ReadinessState.READY if self.ready() else ReadinessState.NOT_READY,
            liveness=LivenessState.ALIVE,
            state=HealthState.HEALTHY,
            version=VersionInfo(version_id=self.version()),
            generated_at=utc_now(),
        )

    def status(self) -> HealthState:
        return HealthState.HEALTHY

    def metrics(self) -> dict[str, Any]:
        return {"ready": self._ready}

    def dependencies(self) -> tuple[str, ...]:
        return ()

    def ready(self) -> bool:
        return self._ready
