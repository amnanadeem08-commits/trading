"""Unit tests for market data lifecycle."""

from __future__ import annotations

from events.event_bus import EventBus
from market_data import MarketLifecycleEventType, MarketLifecycleManager
from metrics.registry import MetricRegistry


def test_lifecycle_emit_events() -> None:
    bus = EventBus()
    metrics = MetricRegistry()
    lifecycle = MarketLifecycleManager(event_bus=bus, metrics=metrics)
    lifecycle.emit(
        MarketLifecycleEventType.DATASET_REGISTERED,
        dataset_id="dataset-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="registered",
    )
    assert len(lifecycle.events) == 1
    assert lifecycle.events[0].event_type == MarketLifecycleEventType.DATASET_REGISTERED
    assert bus.persistence.count() >= 1


def test_lifecycle_handler_subscription() -> None:
    bus = EventBus()
    metrics = MetricRegistry()
    lifecycle = MarketLifecycleManager(event_bus=bus, metrics=metrics)
    received: list[str] = []

    def handler(event) -> None:
        received.append(event.dataset_id)

    subscription = lifecycle.on_event(handler)
    lifecycle.emit(
        MarketLifecycleEventType.STREAM_STARTED,
        dataset_id="dataset-2",
        correlation_id="corr-2",
        trace_id="trace-2",
        message="stream started",
    )
    lifecycle.off_event(subscription)
    assert received == ["dataset-2"]
