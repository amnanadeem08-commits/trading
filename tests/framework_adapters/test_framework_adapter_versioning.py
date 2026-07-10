"""Unit tests for adapter versioning."""

from __future__ import annotations

import pytest

from framework_adapters import AdapterVersionRegistry, FrameworkAdapterError


@pytest.mark.unit
def test_adapter_version_registry_register_and_latest() -> None:
    registry = AdapterVersionRegistry()
    registry.register(version_id="v1", framework_schema="1.0.0", configuration_hash="abc")
    latest = registry.latest()
    assert latest is not None
    assert latest.version_id == "v1"


@pytest.mark.unit
def test_adapter_version_registry_get_missing() -> None:
    registry = AdapterVersionRegistry()
    with pytest.raises(FrameworkAdapterError):
        registry.get("missing")
