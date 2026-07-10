"""Unit tests for artifact registry."""

from __future__ import annotations

import pytest

from artifact_management import ArtifactNotFoundError, ArtifactRegistry, ArtifactState
from tests.artifact_management_helpers import STUB_ARTIFACT_ID, make_stub_artifact_bundle


@pytest.mark.unit
def test_artifact_registry_register_and_lookup() -> None:
    registry = ArtifactRegistry()
    reference, metadata, manifest = make_stub_artifact_bundle(artifact_id="artifact-1")
    record = registry.register(metadata=metadata, manifest=manifest, reference=reference)
    assert record.artifact_id == "artifact-1"
    assert record.state == ArtifactState.REGISTERED
    assert registry.lookup("artifact-1").artifact_id == "artifact-1"


@pytest.mark.unit
def test_artifact_registry_update_state_and_clear() -> None:
    registry = ArtifactRegistry()
    reference, metadata, manifest = make_stub_artifact_bundle()
    registry.register(metadata=metadata, manifest=manifest, reference=reference)
    registry.update_state(STUB_ARTIFACT_ID, ArtifactState.CACHED)
    assert registry.lookup(STUB_ARTIFACT_ID).state == ArtifactState.CACHED
    registry.clear()
    assert registry.list() == ()


@pytest.mark.unit
def test_artifact_registry_lookup_missing() -> None:
    registry = ArtifactRegistry()
    with pytest.raises(ArtifactNotFoundError):
        registry.lookup("missing")
