"""Unit tests for plugin lifecycle."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from ml_engine_plugins import PluginLifecycleEventType, PluginLifecycleManager


@pytest.mark.unit
def test_plugin_lifecycle_discovered_and_registered() -> None:
    lifecycle = PluginLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_plugin_discovered(
        plugin_id="engine-1",
        name="Stub",
        version="1.0.0",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_plugin_registered(
        plugin_id="engine-1",
        name="Stub",
        version="1.0.0",
        correlation_id="c",
        trace_id="t",
    )
    types = {event.event_type for event in lifecycle.events}
    assert PluginLifecycleEventType.PLUGIN_DISCOVERED in types
    assert PluginLifecycleEventType.PLUGIN_REGISTERED in types
