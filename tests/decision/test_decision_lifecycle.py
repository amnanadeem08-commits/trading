"""Unit tests for decision lifecycle manager."""

from __future__ import annotations

from decision import DecisionLifecycleEventType, DecisionLifecycleManager
from events.event_bus import EventBus
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context


def test_lifecycle_emit_events() -> None:
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
    lifecycle = DecisionLifecycleManager(context)

    lifecycle.emit(
        DecisionLifecycleEventType.DECISION_STARTED,
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="started",
    )
    lifecycle.emit(
        DecisionLifecycleEventType.DECISION_COMPLETED,
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="completed",
    )
    assert len(lifecycle.events) == 2
    assert lifecycle.events[0].event_type == DecisionLifecycleEventType.DECISION_STARTED
    assert bus.persistence.count() >= 2


def test_lifecycle_handler_subscription() -> None:
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
    lifecycle = DecisionLifecycleManager(context)
    received: list[str] = []

    subscription_id = lifecycle.on_event(lambda event: received.append(event.decision_id))
    lifecycle.emit(
        DecisionLifecycleEventType.DECISION_REJECTED,
        decision_id="dec-2",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="rejected",
    )
    lifecycle.off_event(subscription_id)
    lifecycle.emit(
        DecisionLifecycleEventType.DECISION_FAILED,
        decision_id="dec-3",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="failed",
    )
    assert received == ["dec-2"]


def test_lifecycle_all_event_types() -> None:
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
    lifecycle = DecisionLifecycleManager(context)

    for event_type in DecisionLifecycleEventType:
        lifecycle.emit(
            event_type,
            decision_id="dec-1",
            correlation_id="corr-1",
            trace_id="trace-1",
            message=event_type.value,
        )
    assert len(lifecycle.events) == 4
