"""Unit tests for ML lifecycle manager."""

from __future__ import annotations

import pytest

from core import CoreRuntime, reset_core_runtime
from events.event_bus import EventBus
from ml import MLLifecycleEventType, MLLifecycleManager
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_core_runtime()
    yield
    reset_application_context()
    reset_core_runtime()


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
    lifecycle = MLLifecycleManager(context)
    lifecycle.emit(
        MLLifecycleEventType.TRAINING_STARTED,
        model_id="sample-model",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="training started",
    )
    assert len(lifecycle.events) == 1
    assert bus.persistence.count() == 1


@pytest.mark.unit
def test_lifecycle_subscription_cleanup() -> None:
    context = build_pipeline_context()
    lifecycle = MLLifecycleManager(context)
    events: list[str] = []

    def handler(event) -> None:
        events.append(event.event_type.value)

    subscription_id = lifecycle.on_event(handler)
    lifecycle.emit(
        MLLifecycleEventType.MODEL_REGISTERED,
        model_id="sample-model",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="registered",
    )
    lifecycle.off_event(subscription_id)
    lifecycle.emit(
        MLLifecycleEventType.INFERENCE_COMPLETED,
        model_id="sample-model",
        correlation_id="corr-2",
        trace_id="trace-1",
        message="inference done",
    )
    assert events == ["model_registered"]


@pytest.mark.unit
def test_lifecycle_integrates_with_core_runtime() -> None:
    runtime = CoreRuntime(context=build_pipeline_context())
    core_context = runtime.initialize()
    lifecycle = MLLifecycleManager(runtime.pipeline_context)
    lifecycle.emit(
        MLLifecycleEventType.EVALUATION_COMPLETED,
        model_id="sample-model",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="evaluation completed",
    )
    assert lifecycle.events[0].trace_id == core_context.trace_id
