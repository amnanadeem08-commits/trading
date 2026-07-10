"""Unit tests for feature store lifecycle."""

from __future__ import annotations

from events.event_bus import EventBus
from feature_store import FeatureStoreLifecycleEventType, FeatureStoreLifecycleManager
from metrics.registry import MetricRegistry


def test_lifecycle_emit_and_handlers() -> None:
    bus = EventBus()
    metrics = MetricRegistry()
    lifecycle = FeatureStoreLifecycleManager(event_bus=bus, metrics=metrics)
    received: list[str] = []

    def handler(event) -> None:
        received.append(event.dataset_id)

    subscription = lifecycle.on_event(handler)
    lifecycle.emit(
        FeatureStoreLifecycleEventType.DATASET_CREATED,
        dataset_id="dataset-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="created",
    )
    lifecycle.off_event(subscription)
    assert received == ["dataset-1"]
    assert len(lifecycle.events) == 1


def test_lifecycle_dataset_updated_event() -> None:
    bus = EventBus()
    metrics = MetricRegistry()
    lifecycle = FeatureStoreLifecycleManager(event_bus=bus, metrics=metrics)
    updated = lifecycle.emit_dataset_updated(
        dataset_id="dataset-1",
        record_count=5,
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    assert updated.record_count == 5
    assert lifecycle.events[-1].event_type == FeatureStoreLifecycleEventType.DATASET_UPDATED
