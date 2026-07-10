"""Plugin metrics collection."""

from __future__ import annotations

from threading import RLock

from ml_engine_plugins.plugin_state import PluginState
from ml_engine_plugins.plugin_statistics import PluginStatistics
from ml_engine_plugins.plugin_summary import PluginSummary


class PluginMetricsCollector:
    """Collects plugin framework metrics without external backends."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._state_counts: dict[PluginState, int] = {state: 0 for state in PluginState}
        self._summaries: dict[str, PluginSummary] = {}

    def record_state(self, state: PluginState) -> None:
        with self._lock:
            self._state_counts[state] = self._state_counts.get(state, 0) + 1

    def record_summary(self, summary: PluginSummary) -> None:
        with self._lock:
            self._summaries[summary.plugin_id] = summary

    def statistics(self) -> PluginStatistics:
        with self._lock:
            total = sum(self._state_counts.values())
            return PluginStatistics(
                total_plugins=total,
                discovered_plugins=self._state_counts.get(PluginState.DISCOVERED, 0),
                registered_plugins=self._state_counts.get(PluginState.REGISTERED, 0),
                loaded_plugins=self._state_counts.get(PluginState.LOADED, 0),
                validated_plugins=self._state_counts.get(PluginState.VALIDATED, 0),
                healthy_plugins=self._state_counts.get(PluginState.HEALTHY, 0),
                failed_plugins=self._state_counts.get(PluginState.FAILED, 0),
                unloaded_plugins=self._state_counts.get(PluginState.UNLOADED, 0),
            )

    def get_summary(self, plugin_id: str) -> PluginSummary | None:
        with self._lock:
            return self._summaries.get(plugin_id)
