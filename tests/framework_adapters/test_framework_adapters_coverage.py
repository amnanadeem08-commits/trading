"""Coverage tests for framework adapters."""

from __future__ import annotations

import pytest

from framework_adapters import (
    AdapterLifecycleEventType,
    AdapterResolutionError,
    AdapterVersionRegistry,
    EngineType,
    FrameworkAdapterError,
    create_stub_adapter,
)
from framework_adapters.contracts.adapter_manifest import AdapterManifest
from framework_adapters.contracts.adapter_metadata import AdapterMetadata
from framework_adapters.validation.validator import FrameworkAdapterValidator
from tests.framework_adapters_helpers import make_resolver_with_stub, make_stub_framework_adapter


@pytest.mark.unit
def test_stub_adapter_contract_methods() -> None:
    adapter = create_stub_adapter()
    assert adapter.adapter_id()
    assert adapter.engine_type() == EngineType.STUB
    assert adapter.metadata().adapter_id == adapter.adapter_id()
    assert adapter.manifest().adapter_id == adapter.adapter_id()
    assert adapter.capabilities()
    assert adapter.validate_environment()["status"] == "healthy"
    assert adapter.load_artifact(artifact_reference="ref", metadata={})["loaded"] is True
    executor = adapter.create_executor()
    assert executor.executor_id()
    adapter.shutdown()


@pytest.mark.unit
def test_resolver_manifest_metadata_mismatch() -> None:
    resolver = make_resolver_with_stub()
    metadata = make_stub_framework_adapter().metadata()
    manifest = AdapterManifest(
        adapter_id="other",
        name="Other",
        version="1.0.0",
        engine_type=EngineType.PYTORCH,
    )
    with pytest.raises(AdapterResolutionError):
        resolver.resolve(engine_type=EngineType.STUB, manifest=manifest, metadata=metadata)


@pytest.mark.unit
def test_validator_metadata_and_manifest_checks() -> None:
    validator = FrameworkAdapterValidator()
    bad_metadata = AdapterMetadata(adapter_id="", name="", version="")
    bad_manifest = AdapterManifest(adapter_id="", name="", version="")
    assert validator.validate_metadata(bad_metadata).valid is False
    assert validator.validate_manifest(bad_manifest).valid is False


@pytest.mark.unit
def test_version_registry_rejects_empty_id() -> None:
    registry = AdapterVersionRegistry()
    with pytest.raises(FrameworkAdapterError):
        registry.register(version_id="", framework_schema="1.0.0")


@pytest.mark.unit
def test_lifecycle_failed_and_shutdown_event_types_exist() -> None:
    assert AdapterLifecycleEventType.ADAPTER_FAILED.value == "adapter_failed"
    assert AdapterLifecycleEventType.ADAPTER_SHUTDOWN.value == "adapter_shutdown"
