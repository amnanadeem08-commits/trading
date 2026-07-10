"""Plugin registry."""

from __future__ import annotations

from threading import RLock

from ml_engine_plugins.exceptions import PluginNotFoundError
from ml_engine_plugins.plugin import MLPlugin
from ml_engine_plugins.plugin_record import PluginRecord
from ml_engine_plugins.plugin_state import PluginState
from models.common import utc_now


class PluginRegistry:
    """Thread-safe registry for ML engine plugins."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._plugins: dict[str, MLPlugin] = {}
        self._records: dict[str, PluginRecord] = {}

    def register(self, plugin: MLPlugin) -> PluginRecord:
        plugin_id = plugin.plugin_id()
        metadata = plugin.metadata()
        manifest = plugin.manifest()
        now = utc_now()
        record = PluginRecord(
            plugin_id=plugin_id,
            metadata=metadata,
            manifest=manifest,
            state=PluginState.REGISTERED,
            registered_at=now,
            updated_at=now,
        )
        with self._lock:
            self._plugins[plugin_id] = plugin
            self._records[plugin_id] = record
        return record

    def lookup(self, plugin_id: str) -> PluginRecord:
        with self._lock:
            record = self._records.get(plugin_id)
        if record is None:
            raise PluginNotFoundError(plugin_id)
        return record

    def get_plugin(self, plugin_id: str) -> MLPlugin:
        with self._lock:
            plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise PluginNotFoundError(plugin_id)
        return plugin

    def list(self) -> tuple[PluginRecord, ...]:
        with self._lock:
            return tuple(self._records[pid] for pid in sorted(self._records))

    def update_state(self, plugin_id: str, state: PluginState) -> PluginRecord:
        with self._lock:
            record = self._records.get(plugin_id)
            if record is None:
                raise PluginNotFoundError(plugin_id)
            updated = record.model_copy(update={"state": state, "updated_at": utc_now()})
            self._records[plugin_id] = updated
            return updated

    def clear(self) -> None:
        with self._lock:
            self._plugins.clear()
            self._records.clear()
