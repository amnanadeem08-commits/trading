"""Plugin registry."""

from __future__ import annotations

from threading import RLock

from plugins.exceptions import PluginNotFoundError, PluginRegistrationError
from plugins.plugin import Plugin
from plugins.validation import PluginValidationResult, validate_plugin

_default_registry: PluginRegistry | None = None
_registry_lock = RLock()


class PluginRegistry:
    """Thread-safe registry for plugin definitions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        """Register a plugin definition."""
        plugin_id = plugin.plugin_id
        if not plugin_id.strip():
            msg = "Plugin id must not be empty"
            raise PluginRegistrationError(msg)
        with self._lock:
            if plugin_id in self._plugins:
                msg = f"Plugin already registered: {plugin_id}"
                raise PluginRegistrationError(msg)
            self._plugins[plugin_id] = plugin

    def unregister(self, plugin_id: str) -> None:
        with self._lock:
            if plugin_id not in self._plugins:
                raise PluginNotFoundError(plugin_id)
            del self._plugins[plugin_id]

    def resolve(self, plugin_id: str) -> Plugin:
        with self._lock:
            plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise PluginNotFoundError(plugin_id)
        return plugin

    def exists(self, plugin_id: str) -> bool:
        with self._lock:
            return plugin_id in self._plugins

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._plugins.keys()))

    def all(self) -> tuple[Plugin, ...]:
        with self._lock:
            return tuple(self._plugins[plugin_id] for plugin_id in sorted(self._plugins))

    def validate(
        self,
        plugin: Plugin,
        *,
        platform_version: str,
        platform_api_version: str,
        installed_versions: dict[str, str] | None = None,
    ) -> PluginValidationResult:
        """Validate a plugin against currently registered plugins."""
        with self._lock:
            registered = tuple(self._plugins.values())
        return validate_plugin(
            plugin,
            platform_version=platform_version,
            platform_api_version=platform_api_version,
            installed_versions=installed_versions,
            registered_plugins=registered,
        )


def get_plugin_registry() -> PluginRegistry:
    """Return the process-wide default plugin registry."""
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = PluginRegistry()
        return _default_registry


def reset_plugin_registry() -> None:
    """Reset the default plugin registry. Intended for tests."""
    global _default_registry
    with _registry_lock:
        _default_registry = None
