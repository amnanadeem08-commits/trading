"""Unit tests for execution lifecycle manager."""

from __future__ import annotations

from events.event_bus import EventBus
from execution import ExecutionLifecycleEventType, ExecutionLifecycleManager
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context


def _build_lifecycle() -> ExecutionLifecycleManager:
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
    return ExecutionLifecycleManager(build_pipeline_context(updated_app))


def test_lifecycle_emit_events() -> None:
    lifecycle = _build_lifecycle()
    lifecycle.emit(
        ExecutionLifecycleEventType.EXECUTION_STARTED,
        execution_id="exec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="started",
    )
    lifecycle.emit(
        ExecutionLifecycleEventType.EXECUTION_COMPLETED,
        execution_id="exec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="completed",
    )
    assert len(lifecycle.events) == 2


def test_lifecycle_handler_subscription() -> None:
    lifecycle = _build_lifecycle()
    received: list[str] = []
    subscription_id = lifecycle.on_event(lambda event: received.append(event.execution_id))
    lifecycle.emit(
        ExecutionLifecycleEventType.EXECUTION_DISPATCHED,
        execution_id="exec-2",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="dispatched",
    )
    lifecycle.off_event(subscription_id)
    lifecycle.emit(
        ExecutionLifecycleEventType.EXECUTION_FAILED,
        execution_id="exec-3",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="failed",
    )
    assert received == ["exec-2"]


def test_lifecycle_all_event_types() -> None:
    lifecycle = _build_lifecycle()
    for event_type in ExecutionLifecycleEventType:
        lifecycle.emit(
            event_type,
            execution_id="exec-1",
            correlation_id="corr-1",
            trace_id="trace-1",
            message=event_type.value,
        )
    assert len(lifecycle.events) == 7
