"""Unit tests for provider health."""

from __future__ import annotations

import pytest

from storage_providers import (
    HealthStatus,
    ProviderHealthChecker,
    ProviderRegistry,
    ProviderState,
)
from tests.storage_providers_helpers import STUB_PROVIDER_ID, make_stub_storage_provider


@pytest.mark.unit
def test_provider_health_checker_reports_healthy() -> None:
    registry = ProviderRegistry()
    registry.register(make_stub_storage_provider())
    checker = ProviderHealthChecker(registry=registry)
    result = checker.check(STUB_PROVIDER_ID)
    assert result.status == HealthStatus.HEALTHY


@pytest.mark.unit
def test_provider_health_checker_reports_unhealthy_for_failed_state() -> None:
    registry = ProviderRegistry()
    registry.register(make_stub_storage_provider())
    registry.update_state(STUB_PROVIDER_ID, ProviderState.FAILED)
    checker = ProviderHealthChecker(registry=registry)
    result = checker.check(STUB_PROVIDER_ID)
    assert result.status == HealthStatus.UNHEALTHY
