"""Unit tests for core lifecycle."""

from __future__ import annotations

import pytest

from core import CoreLifecycleEventType, CoreLifecycleManager
from events.event_bus import EventBus
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    yield
    reset_application_context()


@pytest.mark.unit
def test_lifecycle_emits_and_publishes_to_event_bus() -> None:
    bus = EventBus()
    application = build_application_context()
    updated_app = ApplicationContext(
        settings=application.settings,
        feature_flags=application.feature_flags,
        event_bus=bus,
        metrics=application.metrics,
        health=application.health,
        audit=application.audit,
        version_registry=application.version_registry,
        logger_factory=application.logger_factory,
        configuration_hash=application.configuration_hash,
    )
    context = build_pipeline_context(updated_app)
    lifecycle = CoreLifecycleManager(context)
    lifecycle.emit(
        CoreLifecycleEventType.OPERATION_STARTED,
        entity_id="sample-entity",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="started",
    )
    assert len(lifecycle.events) == 1
    assert bus.persistence.count() == 1


@pytest.mark.unit
def test_lifecycle_subscription_cleanup() -> None:
    context = build_pipeline_context()
    lifecycle = CoreLifecycleManager(context)
    events: list[str] = []

    def handler(event) -> None:
        events.append(event.event_type.value)

    subscription_id = lifecycle.on_event(handler)
    lifecycle.emit(
        CoreLifecycleEventType.ENTITY_REGISTERED,
        entity_id="sample-entity",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="registered",
    )
    lifecycle.off_event(subscription_id)
    lifecycle.emit(
        CoreLifecycleEventType.ENTITY_VALIDATED,
        entity_id="sample-entity",
        correlation_id="corr-2",
        trace_id="trace-1",
        message="validated",
    )
    assert events == ["entity_registered"]
