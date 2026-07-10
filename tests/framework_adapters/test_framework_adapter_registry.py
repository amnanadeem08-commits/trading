"""Unit tests for adapter registry."""

from __future__ import annotations

import pytest

from framework_adapters import AdapterNotFoundError, AdapterRegistry, AdapterState
from tests.framework_adapters_helpers import make_stub_framework_adapter


@pytest.mark.unit
def test_adapter_registry_register_and_lookup() -> None:
    registry = AdapterRegistry()
    adapter = make_stub_framework_adapter(adapter_id="adapter-1")
    record = registry.register(adapter)
    assert record.adapter_id == "adapter-1"
    assert record.state == AdapterState.REGISTERED
    assert registry.lookup("adapter-1").adapter_id == "adapter-1"


@pytest.mark.unit
def test_adapter_registry_update_state_and_clear() -> None:
    registry = AdapterRegistry()
    registry.register(make_stub_framework_adapter())
    registry.update_state("stub-engine", AdapterState.LOADED)
    assert registry.lookup("stub-engine").state == AdapterState.LOADED
    registry.clear()
    assert registry.list() == ()


@pytest.mark.unit
def test_adapter_registry_lookup_missing() -> None:
    registry = AdapterRegistry()
    with pytest.raises(AdapterNotFoundError):
        registry.lookup("missing")
