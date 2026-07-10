"""Unit tests for artifact management storage bridge."""

from __future__ import annotations

import pytest

from framework_adapters import create_stub_adapter
from ml_engine_plugins.engines.stub_executor import StubModelExecutor
from storage_providers import (
    STUB_LOCAL_PROVIDER_ID,
    ProviderLifecycleEventType,
    ProviderResolutionError,
    ProviderState,
    build_storage_bridge,
)
from tests.artifact_management_helpers import make_stub_artifact_bundle
from tests.storage_providers_helpers import (
    make_storage_bridge_with_artifact_bundle,
)


@pytest.mark.unit
def test_storage_bridge_auto_registers_stub_local_provider() -> None:
    bridge, _, _, _ = make_storage_bridge_with_artifact_bundle()
    record = bridge.provider_registry.lookup(STUB_LOCAL_PROVIDER_ID)
    assert record.state == ProviderState.REGISTERED


@pytest.mark.unit
def test_storage_bridge_resolve_through_provider() -> None:
    bridge, reference, metadata, manifest = make_storage_bridge_with_artifact_bundle()
    resolved = bridge.resolve_through_provider(
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    assert resolved.attributes["provider_id"] == STUB_LOCAL_PROVIDER_ID
    assert resolved.location is not None
    assert resolved.location.scheme.value == "local"


@pytest.mark.unit
def test_storage_bridge_load_through_adapter() -> None:
    bridge, reference, metadata, manifest = make_storage_bridge_with_artifact_bundle()
    adapter = create_stub_adapter()
    executor = bridge.load_through_adapter(
        adapter,
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    assert isinstance(executor, StubModelExecutor)


@pytest.mark.unit
def test_storage_bridge_shutdown_provider() -> None:
    bridge, _, _, _ = make_storage_bridge_with_artifact_bundle()
    bridge.shutdown_provider(STUB_LOCAL_PROVIDER_ID)
    assert bridge.provider_registry.lookup(STUB_LOCAL_PROVIDER_ID).state == ProviderState.SHUTDOWN
    assert (
        bridge.provider_lifecycle.events[-1].event_type
        == ProviderLifecycleEventType.PROVIDER_SHUTDOWN
    )


@pytest.mark.unit
def test_storage_bridge_register_provider_rejects_invalid_type() -> None:
    bridge, _, _, _ = make_storage_bridge_with_artifact_bundle()
    with pytest.raises(TypeError):
        bridge.register_provider(object())


@pytest.mark.unit
def test_storage_bridge_resolve_fails_without_provider() -> None:
    bridge = build_storage_bridge(auto_register_defaults=False)
    reference, metadata, manifest = make_stub_artifact_bundle()
    with pytest.raises(ProviderResolutionError):
        bridge.resolve_through_provider(
            reference=reference,
            metadata=metadata,
            manifest=manifest,
        )


@pytest.mark.unit
def test_storage_bridge_records_cache_miss_then_hit() -> None:
    bridge, reference, metadata, manifest = make_storage_bridge_with_artifact_bundle()
    bridge.resolve_through_provider(reference=reference, metadata=metadata, manifest=manifest)
    bridge.load_through_adapter(
        create_stub_adapter(),
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    bridge.resolve_through_provider(reference=reference, metadata=metadata, manifest=manifest)
    stats = bridge.provider_metrics_collector.statistics()
    assert stats.cache_misses >= 1
    assert stats.cache_hits >= 1


@pytest.mark.unit
def test_storage_bridge_default_lifecycle_events() -> None:
    bridge, reference, metadata, manifest = make_storage_bridge_with_artifact_bundle()
    bridge.resolve_through_provider(reference=reference, metadata=metadata, manifest=manifest)
    event_types = {event.event_type for event in bridge.provider_lifecycle.events}
    assert ProviderLifecycleEventType.PROVIDER_REGISTERED in event_types
    assert ProviderLifecycleEventType.PROVIDER_VALIDATED in event_types
    assert ProviderLifecycleEventType.PROVIDER_RESOLVED in event_types
