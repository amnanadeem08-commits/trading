"""Unit tests for execution versioning."""

from __future__ import annotations

from execution import ExecutionVersion
from versioning.strategy_registry import reset_strategy_registry


def test_execution_version_register() -> None:
    reset_strategy_registry()
    version = ExecutionVersion(
        execution_id="contract-1",
        version_id="1.0.0",
        description="Initial version",
    )
    registered = version.register()
    assert registered.version_id == "1.0.0"
    versions = ExecutionVersion.list_versions()
    assert len(versions) >= 1


def test_execution_version_to_version_info() -> None:
    version = ExecutionVersion(
        execution_id="contract-1",
        version_id="2.0.0",
        artifact_type="contract",
        description="Updated",
    )
    info = version.to_version_info()
    assert info.version_id == "2.0.0"


def test_execution_version_is_compatible() -> None:
    reset_strategy_registry()
    version = ExecutionVersion(
        execution_id="contract-1",
        version_id="1.0.0",
    )
    assert version.is_compatible() is True
    version.register()
    assert version.is_compatible() is True
