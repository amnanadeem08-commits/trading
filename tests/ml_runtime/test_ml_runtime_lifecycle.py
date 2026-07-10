"""Unit tests for runtime lifecycle."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from ml_runtime import RuntimeLifecycleEventType, RuntimeLifecycleManager


@pytest.mark.unit
def test_lifecycle_runtime_initialized() -> None:
    lifecycle = RuntimeLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_runtime_initialized(
        runtime_version="1.0.0",
        correlation_id="c",
        trace_id="t",
    )
    types = {event.event_type for event in lifecycle.events}
    assert RuntimeLifecycleEventType.RUNTIME_INITIALIZED in types


@pytest.mark.unit
def test_lifecycle_executor_events() -> None:
    lifecycle = RuntimeLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_executor_registered(
        executor_id="executor-1",
        name="Stub",
        version="1.0.0",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_executor_loaded(
        executor_id="executor-1",
        artifact_reference="artifact-1",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_executor_unloaded(
        executor_id="executor-1",
        correlation_id="c",
        trace_id="t",
    )
    subscription = lifecycle.on_event(lambda _event: None)
    lifecycle.off_event(subscription)
    types = {event.event_type for event in lifecycle.events}
    assert RuntimeLifecycleEventType.EXECUTOR_REGISTERED in types
    assert RuntimeLifecycleEventType.EXECUTOR_LOADED in types
    assert RuntimeLifecycleEventType.EXECUTOR_UNLOADED in types
