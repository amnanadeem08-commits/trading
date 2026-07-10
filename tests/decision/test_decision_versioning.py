"""Unit tests for decision versioning."""

from __future__ import annotations

from decision import DecisionVersion
from versioning.schema_registry import reset_schema_registry


def test_decision_version_register() -> None:
    reset_schema_registry()
    version = DecisionVersion(
        decision_id="policy-1",
        version_id="1.0.0",
        description="Initial version",
    )
    registered = version.register()
    assert registered.version_id == "1.0.0"
    versions = DecisionVersion.list_versions()
    assert len(versions) >= 1


def test_decision_version_to_version_info() -> None:
    version = DecisionVersion(
        decision_id="policy-1",
        version_id="2.0.0",
        artifact_type="policy",
        description="Updated",
    )
    info = version.to_version_info()
    assert info.version_id == "2.0.0"
    assert info.description == "Updated"
