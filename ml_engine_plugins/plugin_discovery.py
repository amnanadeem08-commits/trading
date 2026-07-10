"""Plugin discovery."""

from __future__ import annotations

from threading import RLock

from ml_engine_plugins.exceptions import PluginDiscoveryError
from ml_engine_plugins.plugin import MLPlugin
from ml_engine_plugins.plugin_lifecycle import PluginLifecycleManager
from ml_engine_plugins.plugin_state import PluginState


class PluginDiscovery:
    """Discovers ML engine plugins from registered providers."""

    def __init__(self, *, lifecycle: PluginLifecycleManager | None = None) -> None:
        self._lock = RLock()
        self._providers: list[MLPlugin] = []
        self._discovered: dict[str, MLPlugin] = {}
        self._lifecycle = lifecycle

    def register_provider(self, plugin: MLPlugin) -> None:
        with self._lock:
            self._providers.append(plugin)

    def discover(self) -> tuple[MLPlugin, ...]:
        discovered: list[MLPlugin] = []
        with self._lock:
            providers = tuple(self._providers)
        for plugin in providers:
            plugin_id = plugin.plugin_id()
            if not plugin_id.strip():
                msg = "plugin_id must not be empty"
                raise PluginDiscoveryError(msg)
            with self._lock:
                self._discovered[plugin_id] = plugin
            discovered.append(plugin)
            if self._lifecycle is not None:
                metadata = plugin.metadata()
                self._lifecycle.emit_plugin_discovered(
                    plugin_id=plugin_id,
                    name=metadata.name,
                    version=metadata.version,
                    correlation_id=plugin_id,
                    trace_id=plugin_id,
                )
        return tuple(discovered)

    def get(self, plugin_id: str) -> MLPlugin | None:
        with self._lock:
            return self._discovered.get(plugin_id)

    def list_discovered(self) -> tuple[MLPlugin, ...]:
        with self._lock:
            return tuple(self._discovered[pid] for pid in sorted(self._discovered))

    def clear(self) -> None:
        with self._lock:
            self._providers.clear()
            self._discovered.clear()

    def mark_registered(self, plugin_id: str) -> None:
        _ = PluginState.REGISTERED
        with self._lock:
            if plugin_id not in self._discovered:
                raise PluginDiscoveryError(f"Plugin not discovered: {plugin_id}")
