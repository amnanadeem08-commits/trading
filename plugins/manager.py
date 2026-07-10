"""Plugin manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from uuid import uuid4

from config.settings import PluginSettings, get_settings
from health.models import HealthState
from models.events import EventType
from pipeline.context import PipelineContext, build_pipeline_context
from plugins.discovery import PluginDiscovery
from plugins.exceptions import PluginNotFoundError, PluginStateError, PluginValidationError
from plugins.lifecycle import PluginLifecycle, PluginLifecycleEventType, PluginLifecycleManager
from plugins.loader import PluginLoader
from plugins.plugin import BasePlugin, LoadedPlugin, Plugin
from plugins.registry import PluginRegistry, get_plugin_registry
from plugins.state import PluginState
from plugins.validation import validate_plugin_set


@dataclass
class PluginResourceHandles:
    """Tracked runtime resources for a loaded plugin."""

    event_bus_subscriptions: tuple[str, ...] = ()
    lifecycle_subscriptions: tuple[str, ...] = ()
    health_component: str | None = None
    metric_names: tuple[str, ...] = field(default_factory=tuple)


_default_manager: PluginManager | None = None
_manager_lock = RLock()


class PluginManager:
    """Coordinates plugin loading, lifecycle, and registry operations."""

    def __init__(
        self,
        *,
        registry: PluginRegistry | None = None,
        context: PipelineContext | None = None,
        settings: PluginSettings | None = None,
        loader: PluginLoader | None = None,
    ) -> None:
        self._context = context or build_pipeline_context()
        self._settings = settings or get_settings().plugins
        self._registry = registry or get_plugin_registry()
        self._loader = loader or PluginLoader(PluginDiscovery())
        self._lifecycle = PluginLifecycleManager(self._context)
        self._lock = RLock()
        self._loaded: dict[str, LoadedPlugin] = {}
        self._runtimes: dict[str, PluginLifecycle] = {}
        self._resources: dict[str, PluginResourceHandles] = {}

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    @property
    def lifecycle(self) -> PluginLifecycleManager:
        return self._lifecycle

    def load(self, plugin: Plugin, implementation: BasePlugin | None = None) -> LoadedPlugin:
        """Load a plugin definition into the manager."""
        correlation_id = str(uuid4())
        validation = validate_plugin_set(
            (*self._registry.all(), plugin),
            platform_version=self._context.settings.schema_version,
            platform_api_version=self._settings.platform_api_version,
            installed_versions=self._installed_versions(),
        )
        if not validation.valid:
            self._lifecycle.emit(
                PluginLifecycleEventType.PLUGIN_FAILED,
                plugin_id=plugin.plugin_id,
                plugin_version=plugin.version,
                correlation_id=correlation_id,
                message="; ".join(validation.errors),
            )
            msg = f"Plugin validation failed: {plugin.plugin_id}"
            raise PluginValidationError(msg, errors=validation.errors)

        self._registry.register(plugin)
        loaded = LoadedPlugin(
            definition=plugin,
            implementation=implementation,
            state=PluginState.LOADED if implementation is not None else PluginState.DISCOVERED,
        )
        with self._lock:
            self._loaded[plugin.plugin_id] = loaded
            if implementation is not None:
                self._runtimes[plugin.plugin_id] = PluginLifecycle(implementation)

        self._lifecycle.emit(
            PluginLifecycleEventType.PLUGIN_LOADED,
            plugin_id=plugin.plugin_id,
            plugin_version=plugin.version,
            correlation_id=correlation_id,
            message="plugin loaded",
        )
        return loaded

    def unload(self, plugin_id: str) -> None:
        """Unload a plugin from the manager and registry."""
        loaded = self._resolve_loaded(plugin_id)
        if loaded.state == PluginState.ENABLED:
            self.disable(plugin_id)
        self._cleanup_resources(plugin_id)
        with self._lock:
            self._loaded.pop(plugin_id, None)
            self._runtimes.pop(plugin_id, None)
            self._resources.pop(plugin_id, None)
        self._registry.unregister(plugin_id)

    def enable(self, plugin_id: str) -> PluginState:
        """Enable a loaded plugin."""
        loaded = self._resolve_loaded(plugin_id)
        runtime = self._resolve_runtime(plugin_id)
        runtime.initialize()
        state = runtime.start()
        with self._lock:
            loaded.state = state
            self._resources[plugin_id] = self._register_observability(plugin_id)
        self._lifecycle.emit(
            PluginLifecycleEventType.PLUGIN_ENABLED,
            plugin_id=plugin_id,
            plugin_version=loaded.definition.version,
            correlation_id=str(uuid4()),
            message="plugin enabled",
        )
        return state

    def disable(self, plugin_id: str) -> PluginState:
        """Disable an enabled plugin."""
        loaded = self._resolve_loaded(plugin_id)
        runtime = self._resolve_runtime(plugin_id)
        runtime.stop()
        state = runtime.dispose()
        with self._lock:
            loaded.state = state
        self._reset_metrics(plugin_id)
        self._lifecycle.emit(
            PluginLifecycleEventType.PLUGIN_DISABLED,
            plugin_id=plugin_id,
            plugin_version=loaded.definition.version,
            correlation_id=str(uuid4()),
            message="plugin disabled",
        )
        return state

    def reload(self, plugin_id: str, plugin: Plugin, implementation: BasePlugin) -> LoadedPlugin:
        """Reload a plugin definition and implementation."""
        if self._registry.exists(plugin_id):
            self.unload(plugin_id)
        return self.load(plugin, implementation)

    def discover(
        self,
        *,
        modules: tuple[str, ...] | None = None,
    ) -> tuple[Plugin, ...]:
        """Discover plugin definitions and emit discovery events."""
        plugins = self._loader.discover(modules=modules)
        correlation_id = str(uuid4())
        for plugin in plugins:
            self._lifecycle.emit(
                PluginLifecycleEventType.PLUGIN_DISCOVERED,
                plugin_id=plugin.plugin_id,
                plugin_version=plugin.version,
                correlation_id=correlation_id,
                message="plugin discovered",
            )
        return plugins

    def get_state(self, plugin_id: str) -> PluginState:
        """Return the current state for a loaded plugin."""
        return self._resolve_loaded(plugin_id).state

    def resource_handles(self, plugin_id: str) -> PluginResourceHandles | None:
        """Return tracked resource handles for a plugin."""
        with self._lock:
            return self._resources.get(plugin_id)

    def _register_observability(self, plugin_id: str) -> PluginResourceHandles:
        health_name = f"plugin:{plugin_id}"
        self._context.health.register(
            health_name,
            lambda: (HealthState.HEALTHY, f"plugin {plugin_id} enabled"),
        )
        enabled_gauge = f"plugin.{plugin_id}.enabled"
        self._context.metrics.gauge(enabled_gauge).set(1)
        event_subscription = self._context.event_bus.subscribe(
            EventType.VALIDATION_COMPLETED,
            lambda _event: None,
        )
        lifecycle_subscription = self._lifecycle.on_event(lambda _event: None)
        return PluginResourceHandles(
            event_bus_subscriptions=(event_subscription,),
            lifecycle_subscriptions=(lifecycle_subscription,),
            health_component=health_name,
            metric_names=(enabled_gauge,),
        )

    def _reset_metrics(self, plugin_id: str) -> None:
        handles = self._resources.get(plugin_id)
        if handles is None:
            return
        for metric_name in handles.metric_names:
            self._context.metrics.gauge(metric_name).set(0)

    def _cleanup_resources(self, plugin_id: str) -> None:
        handles = self._resources.get(plugin_id)
        if handles is None:
            return
        if handles.health_component is not None:
            self._context.health.unregister(handles.health_component)
        for subscription_id in handles.event_bus_subscriptions:
            self._context.event_bus.unsubscribe(subscription_id)
        for subscription_id in handles.lifecycle_subscriptions:
            self._lifecycle.off_event(subscription_id)
        for metric_name in handles.metric_names:
            self._context.metrics.gauge(metric_name).set(0)

    def _resolve_loaded(self, plugin_id: str) -> LoadedPlugin:
        with self._lock:
            loaded = self._loaded.get(plugin_id)
        if loaded is None:
            raise PluginNotFoundError(plugin_id)
        return loaded

    def _resolve_runtime(self, plugin_id: str) -> PluginLifecycle:
        with self._lock:
            runtime = self._runtimes.get(plugin_id)
        if runtime is None:
            raise PluginStateError(plugin_id, PluginState.DISCOVERED.value, "transition")
        return runtime

    def _installed_versions(self) -> dict[str, str]:
        with self._lock:
            return {
                plugin_id: loaded.definition.version for plugin_id, loaded in self._loaded.items()
            }


def get_plugin_manager() -> PluginManager:
    """Return the process-wide default plugin manager."""
    global _default_manager
    with _manager_lock:
        if _default_manager is None:
            _default_manager = PluginManager()
        return _default_manager


def reset_plugin_manager() -> None:
    """Reset the default plugin manager. Intended for tests."""
    global _default_manager
    with _manager_lock:
        _default_manager = None
