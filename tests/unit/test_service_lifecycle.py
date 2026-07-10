"""Unit tests for service lifecycle management."""

from __future__ import annotations

import pytest

from services import (
    LifecycleEventType,
    LifecycleManager,
    ServiceLifecycleError,
    ServiceRegistry,
    build_application_context,
    reset_application_context,
)
from tests.services_fixtures import AlphaService, BetaService


@pytest.fixture(autouse=True)
def _reset_context() -> None:
    reset_application_context()
    yield
    reset_application_context()


@pytest.mark.unit
def test_lifecycle_startup_and_shutdown_order() -> None:
    context = build_application_context()
    registry = ServiceRegistry()
    alpha = AlphaService()
    beta = BetaService(alpha)
    registry.register(alpha)
    registry.register(beta)
    lifecycle = LifecycleManager(registry, context, context.settings.services)

    startup = lifecycle.startup()
    assert startup.success is True
    assert startup.order == ("alpha", "beta")
    assert alpha.ready() is True
    assert beta.ready() is True

    shutdown = lifecycle.shutdown()
    assert shutdown.success is True
    assert shutdown.order == ("beta", "alpha")
    assert alpha.ready() is False
    assert beta.ready() is False


@pytest.mark.unit
def test_lifecycle_emits_events() -> None:
    context = build_application_context()
    registry = ServiceRegistry()
    registry.register(AlphaService())
    lifecycle = LifecycleManager(registry, context, context.settings.services)
    received: list[str] = []
    lifecycle.on_event(lambda event: received.append(event.event_type.value))
    lifecycle.emit_registered(registry.resolve("alpha"))
    lifecycle.startup()
    lifecycle.shutdown()
    assert LifecycleEventType.SERVICE_REGISTERED.value in received
    assert LifecycleEventType.SERVICE_STARTED.value in received
    assert LifecycleEventType.SERVICE_STOPPED.value in received


@pytest.mark.unit
def test_lifecycle_startup_failure_emits_failed_event() -> None:
    context = build_application_context()
    registry = ServiceRegistry()
    alpha = AlphaService()
    alpha._tracker.fail_start = True
    registry.register(alpha)
    lifecycle = LifecycleManager(registry, context, context.settings.services)
    received: list[str] = []
    lifecycle.on_event(lambda event: received.append(event.event_type.value))
    startup = lifecycle.startup()
    assert startup.success is False
    assert LifecycleEventType.SERVICE_FAILED.value in received


@pytest.mark.unit
def test_lifecycle_missing_dependency_fails_startup() -> None:
    context = build_application_context()
    registry = ServiceRegistry()
    registry.register(BetaService(AlphaService()))
    lifecycle = LifecycleManager(registry, context, context.settings.services)
    with pytest.raises(ServiceLifecycleError):
        lifecycle.startup()


@pytest.mark.unit
def test_lifecycle_partial_shutdown_subset() -> None:
    context = build_application_context()
    registry = ServiceRegistry()
    alpha = AlphaService()
    beta = BetaService(alpha)
    registry.register(alpha)
    registry.register(beta)
    lifecycle = LifecycleManager(registry, context, context.settings.services)
    lifecycle.startup()
    result = lifecycle.shutdown(services=("alpha",))
    assert result.success is True
    assert alpha.ready() is False
    assert beta.ready() is True
