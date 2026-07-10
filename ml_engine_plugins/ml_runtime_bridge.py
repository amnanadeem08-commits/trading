"""ML runtime bridge for plugin registration."""

from __future__ import annotations

from collections.abc import Callable

from config.hash import compute_configuration_hash
from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from ml_engine_plugins.health import PluginHealthChecker
from ml_engine_plugins.plugin import MLPlugin
from ml_engine_plugins.plugin_discovery import PluginDiscovery
from ml_engine_plugins.plugin_lifecycle import PluginLifecycleManager
from ml_engine_plugins.plugin_loader import PluginLoader
from ml_engine_plugins.plugin_metrics import PluginMetricsCollector
from ml_engine_plugins.plugin_registry import PluginRegistry
from ml_engine_plugins.plugin_state import PluginState
from ml_engine_plugins.plugin_summary import PluginSummary
from ml_engine_plugins.plugin_version import PluginVersionRegistry
from ml_engine_plugins.validator import PluginValidator
from ml_runtime.execution.model_executor import ModelExecutor
from ml_runtime.runtime.ml_runtime import MLRuntime

type ExecutorRegistrationCallback = Callable[
    [ModelExecutor, str, str, tuple[str, ...]],
    None,
]


class MLRuntimePluginBridge:
    """Bridges plugin discovery into ML runtime via registration callbacks."""

    def __init__(
        self,
        runtime: MLRuntime,
        *,
        event_bus: EventBus | None = None,
        metrics: MetricRegistry | None = None,
        registration_callback: ExecutorRegistrationCallback | None = None,
    ) -> None:
        self._runtime = runtime
        self._event_bus = event_bus or EventBus()
        self._metric_registry = metrics or MetricRegistry()
        self._registration_callback = registration_callback
        self.registry = PluginRegistry()
        self.lifecycle = PluginLifecycleManager(
            event_bus=self._event_bus,
            metrics=self._metric_registry,
        )
        self.discovery = PluginDiscovery(lifecycle=self.lifecycle)
        self.validator = PluginValidator()
        self.loader = PluginLoader(
            registry=self.registry,
            validator=self.validator,
            lifecycle=self.lifecycle,
        )
        self.health_checker = PluginHealthChecker(
            registry=self.registry,
            lifecycle=self.lifecycle,
        )
        self.metrics_collector = PluginMetricsCollector()
        self.version_registry = PluginVersionRegistry()
        self.version_registry.register(
            version_id="ml-engine-plugins-v1",
            framework_schema="1.0.0",
            configuration_hash=compute_configuration_hash(),
        )

    def _register_executor(
        self,
        executor: ModelExecutor,
        *,
        name: str,
        version: str,
        capabilities: tuple[str, ...],
    ) -> None:
        if self._registration_callback is not None:
            self._registration_callback(executor, name, version, capabilities)
        else:
            self._runtime.register_executor(
                executor,
                name=name,
                version=version,
                capabilities=capabilities,
            )

    def discover_and_load(self, plugins: tuple[MLPlugin, ...] | None = None) -> tuple[str, ...]:
        """Discover, validate, load, and register plugins with ML runtime."""
        discovered = plugins if plugins is not None else self.discovery.discover()
        registered: list[str] = []
        for plugin in discovered:
            result = self.validator.validate_plugin(plugin)
            self.validator.ensure_valid(result)
            record = self.loader.load(plugin)
            metadata = plugin.metadata()
            manifest = plugin.manifest()
            executor = plugin.create_executor()
            capability_names = tuple(cap.value for cap in plugin.capabilities())
            self._register_executor(
                executor,
                name=metadata.name,
                version=metadata.version,
                capabilities=capability_names,
            )
            self.lifecycle.emit_plugin_registered(
                plugin_id=plugin.plugin_id(),
                name=metadata.name,
                version=metadata.version,
                correlation_id=plugin.plugin_id(),
                trace_id=plugin.plugin_id(),
            )
            self.metrics_collector.record_state(record.state)
            self.metrics_collector.record_summary(
                PluginSummary(
                    plugin_id=plugin.plugin_id(),
                    name=metadata.name,
                    version=metadata.version,
                    state=PluginState.REGISTERED,
                    engine_type=manifest.engine_type,
                )
            )
            registered.append(plugin.plugin_id())
        return tuple(registered)

    def register_provider(self, plugin: MLPlugin) -> None:
        """Register a plugin provider for discovery."""
        self.discovery.register_provider(plugin)

    def health_check(self, plugin_id: str) -> None:
        """Run health check for a registered plugin."""
        result = self.health_checker.check(plugin_id)
        self.metrics_collector.record_state(PluginState.HEALTHY)
        _ = result

    def unload(self, plugin_id: str) -> None:
        """Unload a plugin from the registry."""
        self.loader.unload(plugin_id)
        self._runtime.registry.unregister_executor(plugin_id)
        self.metrics_collector.record_state(PluginState.UNLOADED)


def build_plugin_bridge(runtime: MLRuntime) -> MLRuntimePluginBridge:
    """Create a plugin bridge bound to an ML runtime."""
    return MLRuntimePluginBridge(runtime)
