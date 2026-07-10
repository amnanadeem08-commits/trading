"""Plugin loader."""

from __future__ import annotations

from ml_engine_plugins.exceptions import PluginLoadError, PluginNotFoundError, PluginValidationError
from ml_engine_plugins.plugin import MLPlugin
from ml_engine_plugins.plugin_lifecycle import PluginLifecycleManager
from ml_engine_plugins.plugin_record import PluginRecord
from ml_engine_plugins.plugin_registry import PluginRegistry
from ml_engine_plugins.plugin_state import PluginState
from ml_engine_plugins.validator import PluginValidator


class PluginLoader:
    """Loads and unloads ML engine plugins into the registry."""

    def __init__(
        self,
        *,
        registry: PluginRegistry,
        validator: PluginValidator | None = None,
        lifecycle: PluginLifecycleManager | None = None,
    ) -> None:
        self._registry = registry
        self._validator = validator or PluginValidator()
        self._lifecycle = lifecycle

    def load(self, plugin: MLPlugin) -> PluginRecord:
        try:
            result = self._validator.validate_plugin(plugin)
            self._validator.ensure_valid(result)
            self._registry.register(plugin)
            loaded = self._registry.update_state(plugin.plugin_id(), PluginState.LOADED)
            if self._lifecycle is not None:
                metadata = plugin.metadata()
                self._lifecycle.emit_plugin_loaded(
                    plugin_id=plugin.plugin_id(),
                    name=metadata.name,
                    version=metadata.version,
                    correlation_id=plugin.plugin_id(),
                    trace_id=plugin.plugin_id(),
                )
                self._lifecycle.emit_plugin_validated(
                    plugin_id=plugin.plugin_id(),
                    correlation_id=plugin.plugin_id(),
                    trace_id=plugin.plugin_id(),
                )
            return loaded
        except Exception as error:
            if self._lifecycle is not None:
                self._lifecycle.emit_plugin_failed(
                    plugin_id=plugin.plugin_id(),
                    message=str(error),
                    correlation_id=plugin.plugin_id(),
                    trace_id=plugin.plugin_id(),
                )
            if isinstance(error, PluginValidationError):
                raise
            msg = f"Failed to load plugin {plugin.plugin_id()}: {error}"
            raise PluginLoadError(msg) from error

    def unload(self, plugin_id: str) -> None:
        try:
            self._registry.get_plugin(plugin_id)
        except PluginNotFoundError as error:
            raise PluginLoadError(str(error)) from error
        self._registry.update_state(plugin_id, PluginState.UNLOADED)
        if self._lifecycle is not None:
            self._lifecycle.emit_plugin_unloaded(
                plugin_id=plugin_id,
                correlation_id=plugin_id,
                trace_id=plugin_id,
            )
