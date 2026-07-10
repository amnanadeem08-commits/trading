"""Unit tests for plugin metrics."""

from __future__ import annotations

import pytest

from ml_engine_plugins import PluginMetricsCollector, PluginState, PluginSummary


@pytest.mark.unit
def test_plugin_metrics_collector() -> None:
    collector = PluginMetricsCollector()
    collector.record_state(PluginState.LOADED)
    collector.record_summary(
        PluginSummary(
            plugin_id="engine-1",
            name="Stub",
            version="1.0.0",
            state=PluginState.LOADED,
        )
    )
    stats = collector.statistics()
    assert stats.loaded_plugins == 1
    assert collector.get_summary("engine-1") is not None
