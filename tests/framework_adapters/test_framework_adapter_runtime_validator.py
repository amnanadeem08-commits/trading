"""Coverage tests for adapter runtime validator."""

from __future__ import annotations

import pytest

from framework_adapters import (
    AdapterRegistry,
    AdapterRuntimeContext,
    AdapterRuntimeValidator,
    EngineType,
    MetadataFrameworkAdapter,
    create_stub_adapter,
)
from framework_adapters.registry.adapter_record import AdapterState
from tests.framework_adapters_helpers import make_adapter_bridge


@pytest.mark.unit
def test_runtime_validator_checks_executor_and_runtime_version() -> None:
    runtime, _bridge = make_adapter_bridge()
    registry = AdapterRegistry()
    adapter = MetadataFrameworkAdapter(
        adapter_id="version-adapter",
        name="Version Adapter",
        version="1.0.0",
        engine_type=EngineType.CUSTOM,
        supported_runtime_versions=("2.0.0",),
    )
    registry.register(adapter)
    validator = AdapterRuntimeValidator(registry=registry)
    record = registry.lookup("version-adapter")

    bad_version = validator.validate_runtime_version(
        record,
        context=AdapterRuntimeContext(engine_type=EngineType.CUSTOM, runtime_version="9.9.9"),
    )
    assert bad_version.valid is False

    missing_executor = validator.validate_executor_available(runtime, executor_id="missing")
    assert missing_executor.valid is False


@pytest.mark.unit
def test_runtime_validator_rejects_failed_adapter_state() -> None:
    registry = AdapterRegistry()
    adapter = create_stub_adapter()
    registry.register(adapter)
    registry.update_state(adapter.adapter_id(), AdapterState.FAILED)
    validator = AdapterRuntimeValidator(registry=registry)
    record = registry.lookup(adapter.adapter_id())
    result = validator.validate_selection(
        record,
        context=AdapterRuntimeContext(engine_type=EngineType.STUB),
    )
    assert result.valid is False
