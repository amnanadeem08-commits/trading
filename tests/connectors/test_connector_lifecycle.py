"""Unit tests for connector lifecycle manager."""

from __future__ import annotations

from connectors import ConnectorLifecycleEventType, ConnectorLifecycleManager
from events.event_bus import EventBus
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context


def _build_lifecycle() -> ConnectorLifecycleManager:
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
    pipeline_context = build_pipeline_context(updated_app)
    return ConnectorLifecycleManager(
        event_bus=pipeline_context.event_bus,
        metrics=pipeline_context.metrics,
    )


def test_lifecycle_emit_events() -> None:
    lifecycle = _build_lifecycle()
    lifecycle.emit(
        ConnectorLifecycleEventType.CONNECTOR_REGISTERED,
        connector_id="conn-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="registered",
    )
    lifecycle.emit(
        ConnectorLifecycleEventType.CONNECTOR_SHUTDOWN,
        connector_id="conn-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="shutdown",
    )
    assert len(lifecycle.events) == 2


def test_lifecycle_handler_subscription() -> None:
    lifecycle = _build_lifecycle()
    received: list[str] = []
    subscription_id = lifecycle.on_event(lambda event: received.append(event.connector_id))
    lifecycle.emit(
        ConnectorLifecycleEventType.CONNECTOR_INITIALIZED,
        connector_id="conn-2",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="initialized",
    )
    lifecycle.off_event(subscription_id)
    lifecycle.emit(
        ConnectorLifecycleEventType.CONNECTOR_VALIDATED,
        connector_id="conn-3",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="validated",
    )
    assert received == ["conn-2"]


def test_lifecycle_all_event_types() -> None:
    lifecycle = _build_lifecycle()
    for event_type in ConnectorLifecycleEventType:
        lifecycle.emit(
            event_type,
            connector_id="conn-1",
            correlation_id="corr-1",
            trace_id="trace-1",
            message=event_type.value,
        )
    assert len(lifecycle.events) == 5
