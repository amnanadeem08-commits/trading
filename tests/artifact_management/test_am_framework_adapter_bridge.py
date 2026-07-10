"""Unit tests for framework adapter artifact bridge."""

from __future__ import annotations

import pytest

from artifact_management import (
    ArtifactLifecycleEventType,
    ArtifactResolutionError,
    ArtifactState,
)
from framework_adapters import create_stub_adapter
from ml_engine_plugins.engines.stub_executor import StubModelExecutor
from storage_providers import ProviderResolutionError
from tests.artifact_management_helpers import (
    STUB_ARTIFACT_ID,
    make_artifact_bridge,
    make_stub_artifact_bundle,
    make_stub_framework_adapter,
)
from tests.storage_providers_helpers import make_storage_bridge


@pytest.mark.unit
def test_framework_adapter_bridge_requires_storage_resolution() -> None:
    bridge = make_artifact_bridge()
    adapter = create_stub_adapter()
    reference, metadata, manifest = make_stub_artifact_bundle(artifact_id=STUB_ARTIFACT_ID)
    with pytest.raises(ArtifactResolutionError):
        bridge.load_through_adapter(
            adapter,
            reference=reference,
            metadata=metadata,
            manifest=manifest,
        )


@pytest.mark.unit
def test_framework_adapter_bridge_load_through_adapter_with_storage_resolution() -> None:
    storage_bridge = make_storage_bridge()
    bridge = storage_bridge.artifact_bridge
    adapter = create_stub_adapter()
    reference, metadata, manifest = make_stub_artifact_bundle(artifact_id=STUB_ARTIFACT_ID)
    executor = storage_bridge.load_through_adapter(
        adapter,
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    assert isinstance(executor, StubModelExecutor)
    assert bridge.registry.lookup(STUB_ARTIFACT_ID).state == ArtifactState.CACHED
    assert bridge.cache.contains(STUB_ARTIFACT_ID)


@pytest.mark.unit
def test_framework_adapter_bridge_lifecycle_and_metrics() -> None:
    storage_bridge = make_storage_bridge()
    bridge = storage_bridge.artifact_bridge
    adapter = create_stub_adapter()
    reference, metadata, manifest = make_stub_artifact_bundle()
    storage_bridge.load_through_adapter(
        adapter,
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert ArtifactLifecycleEventType.ARTIFACT_REGISTERED in event_types
    assert ArtifactLifecycleEventType.ARTIFACT_RESOLVED in event_types
    assert ArtifactLifecycleEventType.ARTIFACT_VALIDATED in event_types
    assert ArtifactLifecycleEventType.ARTIFACT_CACHED in event_types
    stats = bridge.metrics_collector.statistics()
    assert stats.artifact_registrations >= 1
    assert stats.artifact_resolutions >= 1
    assert stats.artifact_validations >= 1


@pytest.mark.unit
def test_framework_adapter_bridge_expire_cached() -> None:
    storage_bridge = make_storage_bridge()
    bridge = storage_bridge.artifact_bridge
    adapter = create_stub_adapter()
    reference, metadata, manifest = make_stub_artifact_bundle()
    storage_bridge.load_through_adapter(
        adapter,
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    bridge.expire_cached(STUB_ARTIFACT_ID)
    assert bridge.registry.lookup(STUB_ARTIFACT_ID).state == ArtifactState.EXPIRED
    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert ArtifactLifecycleEventType.ARTIFACT_EXPIRED in event_types


@pytest.mark.unit
def test_framework_adapter_bridge_validation_failure() -> None:
    storage_bridge = make_storage_bridge()
    adapter = make_stub_framework_adapter()
    reference, metadata, manifest = make_stub_artifact_bundle(uri="invalid")
    with pytest.raises(ProviderResolutionError):
        storage_bridge.load_through_adapter(
            adapter,
            reference=reference,
            metadata=metadata,
            manifest=manifest,
        )
    assert storage_bridge.provider_metrics_collector.statistics().resolution_failures >= 1
