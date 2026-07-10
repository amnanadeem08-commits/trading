"""Unit tests for adapter health."""

from __future__ import annotations

import pytest

from framework_adapters import (
    AdapterRegistry,
    AdapterState,
    FrameworkAdapterHealthChecker,
    HealthStatus,
)
from tests.framework_adapters_helpers import make_stub_framework_adapter


@pytest.mark.unit
def test_adapter_health_checker_reports_healthy() -> None:
    registry = AdapterRegistry()
    registry.register(make_stub_framework_adapter())
    checker = FrameworkAdapterHealthChecker(registry=registry)
    result = checker.check("stub-engine")
    assert result.status == HealthStatus.HEALTHY
    assert registry.lookup("stub-engine").state == AdapterState.HEALTHY


@pytest.mark.unit
def test_adapter_health_checker_unhealthy_failed_state() -> None:
    registry = AdapterRegistry()
    registry.register(make_stub_framework_adapter())
    registry.update_state("stub-engine", AdapterState.FAILED)
    checker = FrameworkAdapterHealthChecker(registry=registry)
    result = checker.check("stub-engine")
    assert result.status == HealthStatus.UNHEALTHY
