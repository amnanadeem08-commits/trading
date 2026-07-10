"""ML engine plugin framework public API."""

from ml_engine_plugins.bootstrap import (
    bootstrap_plugin_runtime,
    lifecycle_event_types,
    register_builtin_plugins,
    run_full_stub_engine_pipeline,
    run_stub_engine_execution,
)
from ml_engine_plugins.engines import (
    STUB_ENGINE_ID,
    STUB_ENGINE_VERSION,
    StubMLEnginePlugin,
    StubModelExecutor,
    create_stub_engine,
)
from ml_engine_plugins.exceptions import (
    MLEnginePluginError,
    PluginDiscoveryError,
    PluginHealthError,
    PluginLoadError,
    PluginNotFoundError,
    PluginValidationError,
)
from ml_engine_plugins.health import PluginHealthChecker
from ml_engine_plugins.health_result import PluginHealthResult, PluginHealthStatus
from ml_engine_plugins.ml_runtime_bridge import MLRuntimePluginBridge, build_plugin_bridge
from ml_engine_plugins.plugin import MLPlugin
from ml_engine_plugins.plugin_capability import PluginCapability
from ml_engine_plugins.plugin_discovery import PluginDiscovery
from ml_engine_plugins.plugin_lifecycle import (
    PluginDiscoveredEvent,
    PluginFailedEvent,
    PluginHealthCheckedEvent,
    PluginLifecycleEvent,
    PluginLifecycleEventType,
    PluginLifecycleManager,
    PluginLoadedEvent,
    PluginRegisteredEvent,
    PluginUnloadedEvent,
    PluginValidatedEvent,
)
from ml_engine_plugins.plugin_loader import PluginLoader
from ml_engine_plugins.plugin_manifest import PluginManifest
from ml_engine_plugins.plugin_metadata import PluginMetadata
from ml_engine_plugins.plugin_metrics import PluginMetricsCollector
from ml_engine_plugins.plugin_record import PluginRecord
from ml_engine_plugins.plugin_registry import PluginRegistry
from ml_engine_plugins.plugin_state import PluginState
from ml_engine_plugins.plugin_statistics import PluginStatistics
from ml_engine_plugins.plugin_summary import PluginSummary
from ml_engine_plugins.plugin_version import PluginVersion, PluginVersionRegistry
from ml_engine_plugins.validation_result import PluginValidationResult
from ml_engine_plugins.validator import PluginValidator

__all__ = [
    "STUB_ENGINE_ID",
    "STUB_ENGINE_VERSION",
    "MLEnginePluginError",
    "MLPlugin",
    "MLRuntimePluginBridge",
    "PluginCapability",
    "PluginDiscoveredEvent",
    "PluginDiscovery",
    "PluginDiscoveryError",
    "PluginFailedEvent",
    "PluginHealthCheckedEvent",
    "PluginHealthChecker",
    "PluginHealthError",
    "PluginHealthResult",
    "PluginHealthStatus",
    "PluginLifecycleEvent",
    "PluginLifecycleEventType",
    "PluginLifecycleManager",
    "PluginLoadError",
    "PluginLoadedEvent",
    "PluginLoader",
    "PluginManifest",
    "PluginMetadata",
    "PluginMetricsCollector",
    "PluginNotFoundError",
    "PluginRecord",
    "PluginRegisteredEvent",
    "PluginRegistry",
    "PluginState",
    "PluginStatistics",
    "PluginSummary",
    "PluginUnloadedEvent",
    "PluginValidatedEvent",
    "PluginValidationError",
    "PluginValidationResult",
    "PluginValidator",
    "PluginVersion",
    "PluginVersionRegistry",
    "StubMLEnginePlugin",
    "StubModelExecutor",
    "bootstrap_plugin_runtime",
    "build_plugin_bridge",
    "create_stub_engine",
    "lifecycle_event_types",
    "register_builtin_plugins",
    "run_full_stub_engine_pipeline",
    "run_stub_engine_execution",
]
