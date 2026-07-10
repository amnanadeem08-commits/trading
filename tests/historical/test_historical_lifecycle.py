"""Unit tests for historical lifecycle."""

from __future__ import annotations

from events.event_bus import EventBus
from historical import HistoricalLifecycleEventType, HistoricalLifecycleManager
from metrics.registry import MetricRegistry


def test_lifecycle_emit_events() -> None:
    bus = EventBus()
    metrics = MetricRegistry()
    lifecycle = HistoricalLifecycleManager(event_bus=bus, metrics=metrics)
    lifecycle.emit(
        HistoricalLifecycleEventType.DATASET_REGISTERED,
        dataset_id="dataset-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="registered",
    )
    assert len(lifecycle.events) == 1
    assert lifecycle.events[0].event_type == HistoricalLifecycleEventType.DATASET_REGISTERED
    assert bus.persistence.count() >= 1


def test_lifecycle_handler_subscription() -> None:
    bus = EventBus()
    metrics = MetricRegistry()
    lifecycle = HistoricalLifecycleManager(event_bus=bus, metrics=metrics)
    received: list[str] = []

    def handler(event) -> None:
        received.append(event.dataset_id)

    subscription = lifecycle.on_event(handler)
    lifecycle.emit(
        HistoricalLifecycleEventType.QUERY_EXECUTED,
        dataset_id="dataset-2",
        correlation_id="corr-2",
        trace_id="trace-2",
        message="query",
    )
    lifecycle.off_event(subscription)
    assert received == ["dataset-2"]
