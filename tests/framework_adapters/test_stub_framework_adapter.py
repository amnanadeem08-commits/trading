"""Unit tests for the concrete stub framework adapter."""

from __future__ import annotations

import pytest

from framework_adapters import (
    STUB_ADAPTER_ID,
    STUB_ADAPTER_VERSION,
    AdapterCapability,
    AdapterFactory,
    AdapterLifecycleEventType,
    AdapterRegistry,
    AdapterState,
    EngineType,
    FrameworkAdapterValidator,
    HealthStatus,
    StubEnvironment,
    StubExecutorFactory,
    StubFrameworkAdapter,
    bootstrap_adapter_runtime,
    create_stub_adapter,
    register_builtin_adapters,
    register_stub_adapter_factory,
)
from ml_engine_plugins.engines.stub_executor import StubModelExecutor
from ml_runtime import ExecutorNotFoundError
from tests.framework_adapters_helpers import make_adapter_bridge, make_stub_plugin


@pytest.mark.unit
def test_stub_framework_adapter_contract_methods() -> None:
    adapter = create_stub_adapter()
    assert adapter.adapter_id() == STUB_ADAPTER_ID
    assert adapter.engine_type() == EngineType.STUB
    assert adapter.metadata().version == STUB_ADAPTER_VERSION
    assert AdapterCapability.LOAD_ARTIFACT in adapter.capabilities()
    environment = adapter.validate_environment()
    assert environment["status"] == "healthy"
    assert environment["python_available"] is True
    assert environment["runtime_supported"] is True
    assert environment["framework_available"] is True
    load_result = adapter.load_artifact(artifact_reference="artifact-1", metadata={"key": "value"})
    assert load_result["loaded"] is True
    assert adapter.artifact_loaded is True
    executor = adapter.create_executor()
    assert isinstance(executor, StubModelExecutor)
    adapter.shutdown()
    assert adapter.artifact_loaded is False


@pytest.mark.unit
def test_stub_environment_deterministic_validation() -> None:
    environment = StubEnvironment()
    result = environment.check_environment()
    assert result["python_available"] is True
    assert result["runtime_supported"] is True
    assert result["framework_available"] is True
    assert result["status"] == "healthy"


@pytest.mark.unit
def test_stub_executor_factory_creates_stub_model_executor() -> None:
    factory = StubExecutorFactory()
    executor = factory.create(executor_id="exec-1")
    assert isinstance(executor, StubModelExecutor)
    assert executor.executor_id() == "exec-1"


@pytest.mark.unit
def test_stub_adapter_factory_registration_and_resolution() -> None:
    factory = AdapterFactory()
    register_stub_adapter_factory(factory)
    adapter = factory.create(EngineType.STUB)
    assert isinstance(adapter, StubFrameworkAdapter)


@pytest.mark.unit
def test_bootstrap_registers_stub_adapter_for_lookup_and_list() -> None:
    _, bridge = bootstrap_adapter_runtime()[:2]
    records = bridge.registry.list()
    adapter_ids = {record.adapter_id for record in records}
    assert STUB_ADAPTER_ID in adapter_ids
    record = bridge.registry.lookup(STUB_ADAPTER_ID)
    assert record.metadata.engine_type == EngineType.STUB
    version = bridge.version_registry.get(STUB_ADAPTER_ID)
    assert version.adapter_id == STUB_ADAPTER_ID


@pytest.mark.unit
def test_validator_checks_environment_manifest_metadata_capabilities() -> None:
    validator = FrameworkAdapterValidator()
    adapter = create_stub_adapter()
    assert validator.validate_metadata(adapter.metadata()).valid is True
    assert validator.validate_manifest(adapter.manifest()).valid is True
    assert validator.validate_capabilities(adapter).valid is True
    assert validator.validate_engine_type(adapter).valid is True
    assert validator.validate_environment(adapter).valid is True
    assert validator.validate_adapter(adapter).valid is True


@pytest.mark.unit
def test_bridge_process_plugin_lifecycle_metrics_and_health() -> None:
    runtime, bridge = make_adapter_bridge()
    register_builtin_adapters(bridge)
    plugin = make_stub_plugin()
    executor = bridge.process_plugin(plugin)
    assert executor.executor_id() == plugin.plugin_id()
    assert runtime.registry.lookup(plugin.plugin_id()).executor_id() == plugin.plugin_id()

    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.ADAPTER_DISCOVERED in event_types
    assert AdapterLifecycleEventType.ADAPTER_REGISTERED in event_types
    assert AdapterLifecycleEventType.ADAPTER_VALIDATED in event_types
    assert AdapterLifecycleEventType.ADAPTER_LOADED in event_types

    stats = bridge.metrics_collector.statistics()
    assert stats.adapter_validations >= 1
    assert stats.adapter_loads >= 1

    health = bridge.health_checker.check(plugin.plugin_id())
    assert health.status == HealthStatus.HEALTHY


@pytest.mark.unit
def test_bridge_shutdown_emits_event_and_records_metrics() -> None:
    runtime, bridge = make_adapter_bridge()
    plugin = make_stub_plugin()
    bridge.process_plugin(plugin)
    bridge.shutdown_adapter(plugin.plugin_id())
    assert bridge.registry.lookup(plugin.plugin_id()).state == AdapterState.SHUTDOWN
    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.ADAPTER_SHUTDOWN in event_types
    assert bridge.metrics_collector.statistics().adapter_shutdowns >= 1
    with pytest.raises(ExecutorNotFoundError):
        runtime.registry.lookup(plugin.plugin_id())


@pytest.mark.unit
def test_duplicate_registration_records_failure() -> None:
    registry = AdapterRegistry()
    validator = FrameworkAdapterValidator(registry=registry)
    adapter = create_stub_adapter()
    registry.register(adapter)
    result = validator.validate_adapter(adapter)
    assert result.valid is False


@pytest.mark.unit
def test_degraded_environment_fails_validation() -> None:
    adapter = StubFrameworkAdapter(environment=StubEnvironment(python_available=False))
    validator = FrameworkAdapterValidator()
    assert validator.validate_environment(adapter).valid is False
