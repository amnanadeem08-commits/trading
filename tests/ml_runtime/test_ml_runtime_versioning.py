"""Unit tests for runtime versioning."""

from __future__ import annotations

import pytest

from ml_runtime import MLRuntimeError, RuntimeVersionRegistry


@pytest.mark.unit
def test_runtime_version_registry() -> None:
    registry = RuntimeVersionRegistry()
    version = registry.register(
        version_id="runtime-v1",
        runtime_schema="1.0.0",
        configuration_hash="hash",
    )
    assert version.version_id == "runtime-v1"
    assert registry.latest() == version
    assert len(registry.list_versions()) == 1


@pytest.mark.unit
def test_runtime_version_registry_errors() -> None:
    registry = RuntimeVersionRegistry()
    with pytest.raises(MLRuntimeError):
        registry.register(version_id="", runtime_schema="1.0.0")
    registry.register(version_id="runtime-v1", runtime_schema="1.0.0")
    with pytest.raises(MLRuntimeError):
        registry.get("missing")
