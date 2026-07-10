"""Unit tests for inference lifecycle."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from inference_pipeline import InferenceLifecycleEventType, InferenceLifecycleManager
from metrics.registry import MetricRegistry


@pytest.mark.unit
def test_lifecycle_queued_and_started() -> None:
    lifecycle = InferenceLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_queued(
        request_id="req-1",
        model_id="model-1",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_started(
        request_id="req-1",
        model_id="model-1",
        version_id="v-1",
        correlation_id="c",
        trace_id="t",
    )
    types = {event.event_type for event in lifecycle.events}
    assert InferenceLifecycleEventType.INFERENCE_QUEUED in types
    assert InferenceLifecycleEventType.INFERENCE_STARTED in types
