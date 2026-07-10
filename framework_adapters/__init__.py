"""Framework adapter foundation public API."""

from framework_adapters.adapters import (
    ORT_ADAPTER_ID,
    ORT_ADAPTER_NAME,
    ORT_ADAPTER_VERSION,
    STUB_ADAPTER_ID,
    STUB_ADAPTER_NAME,
    STUB_ADAPTER_VERSION,
    MetadataFrameworkAdapter,
    OrtFrameworkAdapter,
    StubEnvironment,
    StubExecutorFactory,
    StubFrameworkAdapter,
    create_ort_adapter,
    create_stub_adapter,
)
from framework_adapters.bootstrap import (
    bootstrap_adapter_runtime,
    lifecycle_event_types,
    process_stub_plugin,
    register_builtin_adapters,
    run_full_stub_adapter_pipeline,
    run_stub_adapter_execution,
)
from framework_adapters.contracts.adapter_capability import AdapterCapability
from framework_adapters.contracts.adapter_manifest import AdapterManifest
from framework_adapters.contracts.adapter_metadata import AdapterMetadata
from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.exceptions import (
    AdapterFactoryError,
    AdapterHealthError,
    AdapterLoadError,
    AdapterNotFoundError,
    AdapterResolutionError,
    AdapterValidationError,
    FrameworkAdapterError,
)
from framework_adapters.factory.adapter_factory import AdapterFactory
from framework_adapters.factory.adapter_resolver import AdapterResolver
from framework_adapters.health.adapter_health import FrameworkAdapterHealthChecker
from framework_adapters.health.health_result import FrameworkAdapterHealthResult, HealthStatus
from framework_adapters.health.model_session_health import (
    ModelSessionHealthChecker,
    ModelSessionHealthResult,
)
from framework_adapters.integration.ml_engine_bridge import (
    MLEngineAdapterBridge,
    build_adapter_bridge,
    register_ort_adapter_factory,
    register_stub_adapter_factory,
)
from framework_adapters.lifecycle.adapter_lifecycle import (
    AdapterDiscoveredEvent,
    AdapterFailedEvent,
    AdapterLifecycleEvent,
    AdapterLifecycleEventType,
    AdapterLifecycleManager,
    AdapterLoadedEvent,
    AdapterRegisteredEvent,
    AdapterShutdownEvent,
    AdapterValidatedEvent,
)
from framework_adapters.metrics.adapter_metrics import AdapterMetricsCollector
from framework_adapters.metrics.adapter_statistics import AdapterStatistics
from framework_adapters.metrics.adapter_summary import AdapterSummary
from framework_adapters.registry.adapter_record import AdapterRecord, AdapterState
from framework_adapters.registry.adapter_registry import AdapterRegistry
from framework_adapters.runtime import (
    AdapterRuntime,
    AdapterRuntimeContext,
    AdapterRuntimeSession,
    AdapterRuntimeValidator,
    AdapterSelector,
    ModelRuntimeManager,
    ModelRuntimeState,
    ModelSessionRecord,
    ModelSessionRegistry,
    build_adapter_runtime,
    build_model_session_key,
)
from framework_adapters.validation.validation_result import FrameworkAdapterValidationResult
from framework_adapters.validation.validator import FrameworkAdapterValidator
from framework_adapters.versioning.adapter_version import AdapterVersion, AdapterVersionRegistry

__all__ = [
    "ORT_ADAPTER_ID",
    "ORT_ADAPTER_NAME",
    "ORT_ADAPTER_VERSION",
    "STUB_ADAPTER_ID",
    "STUB_ADAPTER_NAME",
    "STUB_ADAPTER_VERSION",
    "AdapterCapability",
    "AdapterDiscoveredEvent",
    "AdapterFactory",
    "AdapterFactoryError",
    "AdapterFailedEvent",
    "AdapterHealthError",
    "AdapterLifecycleEvent",
    "AdapterLifecycleEventType",
    "AdapterLifecycleManager",
    "AdapterLoadError",
    "AdapterLoadedEvent",
    "AdapterManifest",
    "AdapterMetadata",
    "AdapterMetricsCollector",
    "AdapterNotFoundError",
    "AdapterRecord",
    "AdapterRegisteredEvent",
    "AdapterRegistry",
    "AdapterResolutionError",
    "AdapterResolver",
    "AdapterRuntime",
    "AdapterRuntimeContext",
    "AdapterRuntimeSession",
    "AdapterRuntimeValidator",
    "AdapterSelector",
    "AdapterShutdownEvent",
    "AdapterState",
    "AdapterStatistics",
    "AdapterSummary",
    "AdapterValidatedEvent",
    "AdapterValidationError",
    "AdapterVersion",
    "AdapterVersionRegistry",
    "EngineType",
    "FrameworkAdapter",
    "FrameworkAdapterError",
    "FrameworkAdapterHealthChecker",
    "FrameworkAdapterHealthResult",
    "FrameworkAdapterValidationResult",
    "FrameworkAdapterValidator",
    "HealthStatus",
    "MLEngineAdapterBridge",
    "MetadataFrameworkAdapter",
    "ModelRuntimeManager",
    "ModelRuntimeState",
    "ModelSessionHealthChecker",
    "ModelSessionHealthResult",
    "ModelSessionRecord",
    "ModelSessionRegistry",
    "OrtFrameworkAdapter",
    "StubEnvironment",
    "StubExecutorFactory",
    "StubFrameworkAdapter",
    "bootstrap_adapter_runtime",
    "build_adapter_bridge",
    "build_adapter_runtime",
    "build_model_session_key",
    "create_ort_adapter",
    "create_stub_adapter",
    "lifecycle_event_types",
    "process_stub_plugin",
    "register_builtin_adapters",
    "register_ort_adapter_factory",
    "register_stub_adapter_factory",
    "run_full_stub_adapter_pipeline",
    "run_stub_adapter_execution",
]
