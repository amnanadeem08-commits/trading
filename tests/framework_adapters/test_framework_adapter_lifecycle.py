"""Unit tests for adapter lifecycle."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from framework_adapters import AdapterLifecycleEventType, AdapterLifecycleManager
from metrics.registry import MetricRegistry


@pytest.mark.unit
def test_adapter_lifecycle_emits_events() -> None:
    lifecycle = AdapterLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_adapter_discovered(
        adapter_id="adapter-1",
        name="Stub",
        version="1.0.0",
        correlation_id="corr",
        trace_id="trace",
    )
    lifecycle.emit_adapter_registered(
        adapter_id="adapter-1",
        name="Stub",
        version="1.0.0",
        correlation_id="corr",
        trace_id="trace",
    )
    event_types = {event.event_type for event in lifecycle.events}
    assert AdapterLifecycleEventType.ADAPTER_DISCOVERED in event_types
    assert AdapterLifecycleEventType.ADAPTER_REGISTERED in event_types


@pytest.mark.unit
def test_adapter_lifecycle_handler_subscription() -> None:
    lifecycle = AdapterLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    received: list[str] = []

    def handler(event: object) -> None:
        received.append(event.adapter_id)

    subscription_id = lifecycle.on_event(handler)
    lifecycle.emit_adapter_validated(
        adapter_id="adapter-1",
        correlation_id="corr",
        trace_id="trace",
    )
    lifecycle.off_event(subscription_id)
    assert received == ["adapter-1"]
