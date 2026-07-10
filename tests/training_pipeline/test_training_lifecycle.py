"""Unit tests for training lifecycle."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from training_pipeline import TrainingLifecycleEventType, TrainingLifecycleManager


@pytest.mark.unit
def test_lifecycle_emit_queued() -> None:
    lifecycle = TrainingLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_queued(
        job_id="job-1",
        experiment_id="exp-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    events = lifecycle.events
    assert len(events) == 1
    assert events[0].event_type == TrainingLifecycleEventType.TRAINING_QUEUED


@pytest.mark.unit
def test_lifecycle_handler_subscription() -> None:
    lifecycle = TrainingLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    received: list[str] = []

    def handler(event) -> None:
        received.append(event.job_id)

    lifecycle.on_event(handler)
    lifecycle.emit_started(
        job_id="job-1",
        experiment_id="exp-1",
        run_id="run-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    assert received == ["job-1"]
