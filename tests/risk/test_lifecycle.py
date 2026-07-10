"""Unit tests for risk lifecycle manager."""

from __future__ import annotations

from events.event_bus import EventBus
from pipeline import build_pipeline_context
from risk import RiskLifecycleEventType, RiskLifecycleManager
from services import ApplicationContext, build_application_context


def _build_lifecycle() -> RiskLifecycleManager:
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
    return RiskLifecycleManager(build_pipeline_context(updated_app))


def test_lifecycle_emit_events() -> None:
    lifecycle = _build_lifecycle()
    lifecycle.emit(
        RiskLifecycleEventType.RISK_STARTED,
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="started",
    )
    lifecycle.emit(
        RiskLifecycleEventType.RISK_COMPLETED,
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="completed",
    )
    assert len(lifecycle.events) == 2


def test_lifecycle_handler_subscription() -> None:
    lifecycle = _build_lifecycle()
    received: list[str] = []
    subscription_id = lifecycle.on_event(lambda event: received.append(event.risk_id))
    lifecycle.emit(
        RiskLifecycleEventType.RISK_APPROVED,
        risk_id="risk-2",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="approved",
    )
    lifecycle.off_event(subscription_id)
    lifecycle.emit(
        RiskLifecycleEventType.RISK_REJECTED,
        risk_id="risk-3",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="rejected",
    )
    assert received == ["risk-2"]


def test_lifecycle_all_event_types() -> None:
    lifecycle = _build_lifecycle()
    for event_type in RiskLifecycleEventType:
        lifecycle.emit(
            event_type,
            risk_id="risk-1",
            correlation_id="corr-1",
            trace_id="trace-1",
            message=event_type.value,
        )
    assert len(lifecycle.events) == 5
