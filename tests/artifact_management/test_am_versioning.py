"""Unit tests for artifact versioning."""

from __future__ import annotations

import pytest

from artifact_management import ArtifactManagementError, ArtifactVersionRegistry


@pytest.mark.unit
def test_artifact_version_registry_register_and_latest() -> None:
    registry = ArtifactVersionRegistry()
    registry.register(
        version_id="artifact-v1",
        framework_schema="1.0.0",
        artifact_id="stub-artifact-1",
    )
    latest = registry.latest()
    assert latest is not None
    assert latest.artifact_id == "stub-artifact-1"


@pytest.mark.unit
def test_artifact_version_registry_get_missing() -> None:
    registry = ArtifactVersionRegistry()
    with pytest.raises(ArtifactManagementError):
        registry.get("missing")
