"""ML engine bridge for framework adapter integration."""

from __future__ import annotations

from collections.abc import Callable

from config.hash import compute_configuration_hash
from events.event_bus import EventBus
from framework_adapters.adapters.onnx_framework_adapter import create_ort_adapter
from framework_adapters.adapters.stub_framework_adapter import (
    StubFrameworkAdapter,
    create_stub_adapter,
)
from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.exceptions import AdapterValidationError
from framework_adapters.factory.adapter_factory import AdapterFactory
from framework_adapters.factory.adapter_resolver import AdapterResolver
from framework_adapters.health.adapter_health import FrameworkAdapterHealthChecker
from framework_adapters.lifecycle.adapter_lifecycle import AdapterLifecycleManager
from framework_adapters.metrics.adapter_metrics import AdapterMetricsCollector
from framework_adapters.metrics.adapter_summary import AdapterSummary
from framework_adapters.registry.adapter_record import AdapterState
from framework_adapters.registry.adapter_registry import AdapterRegistry
from framework_adapters.validation.validator import FrameworkAdapterValidator
from framework_adapters.versioning.adapter_version import AdapterVersionRegistry
from metrics.registry import MetricRegistry
from ml_engine_plugins.plugin import MLPlugin
from ml_runtime.execution.model_executor import ModelExecutor
from ml_runtime.runtime.ml_runtime import MLRuntime

type ExecutorRegistrationCallback = Callable[
    [ModelExecutor, str, str, tuple[str, ...]],
    None,
]


def register_stub_adapter_factory(factory: AdapterFactory) -> None:
    """Register the stub adapter factory for EngineType.STUB."""
    factory.register(EngineType.STUB, create_stub_adapter)


def register_ort_adapter_factory(factory: AdapterFactory) -> None:
    """Register the ORT adapter factory for the configured engine type."""
    from framework_adapters.adapters.onnx_framework_adapter import _ort_engine_type

    factory.register(_ort_engine_type(), create_ort_adapter)


class MLEngineAdapterBridge:
    """Bridges ML engine plugins into framework adapters and ML runtime."""

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
        self.registry = AdapterRegistry()
        self.lifecycle = AdapterLifecycleManager(
            event_bus=self._event_bus,
            metrics=self._metric_registry,
        )
        self.factory = AdapterFactory()
        register_stub_adapter_factory(self.factory)
        register_ort_adapter_factory(self.factory)
        self.resolver = AdapterResolver(factory=self.factory)
        self.validator = FrameworkAdapterValidator(registry=self.registry)
        self.health_checker = FrameworkAdapterHealthChecker(registry=self.registry)
        self.metrics_collector = AdapterMetricsCollector()
        self.version_registry = AdapterVersionRegistry()
        self.version_registry.register(
            version_id="framework-adapters-v1",
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

    def register_executor(
        self,
        executor: ModelExecutor,
        *,
        name: str,
        version: str,
        capabilities: tuple[str, ...],
    ) -> None:
        """Register an executor with the bound ML runtime."""
        self._register_executor(
            executor,
            name=name,
            version=version,
            capabilities=capabilities,
        )

    def resolve_engine_type(self, plugin: MLPlugin) -> EngineType:
        """Resolve engine type from plugin manifest."""
        manifest = plugin.manifest()
        return self.resolver.resolve_engine_type(manifest.engine_type)

    def resolve_adapter(
        self,
        plugin: MLPlugin,
    ) -> FrameworkAdapter:
        """Resolve a framework adapter for the given plugin."""
        engine_type = self.resolve_engine_type(plugin)
        return self.resolver.resolve(engine_type=engine_type)

    def process_plugin(
        self,
        plugin: MLPlugin,
        *,
        artifact_reference: str = "",
        artifact_metadata: dict[str, object] | None = None,
    ) -> ModelExecutor:
        """Resolve, validate, register adapter, and return executor for ML runtime."""
        plugin_id = plugin.plugin_id()
        plugin_metadata = plugin.metadata()
        plugin_manifest = plugin.manifest()
        engine_type = self.resolve_engine_type(plugin)

        self.lifecycle.emit_adapter_discovered(
            adapter_id=plugin_id,
            name=plugin_metadata.name,
            version=plugin_metadata.version,
            correlation_id=plugin_id,
            trace_id=plugin_id,
        )

        if engine_type != EngineType.STUB:
            msg = f"Unsupported engine type for stub adapter bridge: {engine_type.value}"
            raise AdapterValidationError(msg)

        adapter = self.resolve_adapter(plugin)
        if adapter.adapter_id() != plugin_id:
            adapter = self._adapt_for_plugin(adapter, plugin_id=plugin_id)

        validation = self.validator.validate_adapter(adapter)
        if not validation.valid:
            self.lifecycle.emit_adapter_failed(
                adapter_id=adapter.adapter_id(),
                message=validation.errors[0] if validation.errors else "validation failed",
                correlation_id=plugin_id,
                trace_id=plugin_id,
            )
            self.metrics_collector.record_failure()
        self.validator.ensure_valid(validation)
        self.lifecycle.emit_adapter_validated(
            adapter_id=adapter.adapter_id(),
            correlation_id=plugin_id,
            trace_id=plugin_id,
        )
        self.metrics_collector.record_state(AdapterState.VALIDATED)
        self.metrics_collector.record_validation()

        record = self.registry.register(adapter)
        self.lifecycle.emit_adapter_registered(
            adapter_id=record.adapter_id,
            name=record.metadata.name,
            version=record.metadata.version,
            correlation_id=plugin_id,
            trace_id=plugin_id,
        )
        self.metrics_collector.record_state(AdapterState.REGISTERED)
        self.metrics_collector.record_summary(
            AdapterSummary(
                adapter_id=record.adapter_id,
                name=record.metadata.name,
                version=record.metadata.version,
                state=AdapterState.REGISTERED,
                engine_type=record.metadata.engine_type,
            )
        )

        load_metadata = artifact_metadata or {
            "plugin_id": plugin_id,
            "engine_type": engine_type.value,
        }
        adapter.load_artifact(
            artifact_reference=artifact_reference or plugin_id,
            metadata=load_metadata,
        )
        self.lifecycle.emit_adapter_loaded(
            adapter_id=adapter.adapter_id(),
            name=record.metadata.name,
            version=record.metadata.version,
            correlation_id=plugin_id,
            trace_id=plugin_id,
        )
        self.registry.update_state(adapter.adapter_id(), AdapterState.LOADED)
        self.metrics_collector.record_state(AdapterState.LOADED)
        self.metrics_collector.record_load()

        executor = adapter.create_executor()
        capability_names = tuple(cap.value for cap in adapter.capabilities())
        self._register_executor(
            executor,
            name=plugin_metadata.name,
            version=plugin_metadata.version,
            capabilities=capability_names,
        )
        _ = plugin_manifest
        return executor

    def _adapt_for_plugin(self, adapter: FrameworkAdapter, *, plugin_id: str) -> FrameworkAdapter:
        if isinstance(adapter, StubFrameworkAdapter):
            return StubFrameworkAdapter(
                adapter_id=plugin_id,
                name=adapter.metadata().name,
                version=adapter.metadata().version,
                executor_id=plugin_id,
            )
        return adapter

    def shutdown_adapter(self, adapter_id: str) -> None:
        """Shutdown and unregister an adapter."""
        adapter = self.registry.get_adapter(adapter_id)
        adapter.shutdown()
        self.lifecycle.emit_adapter_shutdown(
            adapter_id=adapter_id,
            correlation_id=adapter_id,
            trace_id=adapter_id,
        )
        self.registry.update_state(adapter_id, AdapterState.SHUTDOWN)
        self.metrics_collector.record_state(AdapterState.SHUTDOWN)
        self.metrics_collector.record_shutdown()
        self._runtime.registry.unregister_executor(adapter_id)


def build_adapter_bridge(runtime: MLRuntime) -> MLEngineAdapterBridge:
    """Create an adapter bridge bound to an ML runtime."""
    return MLEngineAdapterBridge(runtime)
