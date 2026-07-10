"""Unit tests for adapter registry."""

from __future__ import annotations

import pytest

from connectors import AdapterRegistry, AdapterState, get_adapter_registry, reset_adapter_registry
from connectors.exceptions import AdapterNotFoundError, AdapterRegistrationError
from tests.connectors_helpers import SampleExecutionAdapter, make_adapter_metadata


def test_registry_register_and_resolve() -> None:
    registry = AdapterRegistry()
    registry.register(make_adapter_metadata())
    metadata = registry.resolve("sample-adapter")
    assert metadata.name == "Sample Adapter"


def test_registry_register_type() -> None:
    registry = AdapterRegistry()
    registry.register_type(SampleExecutionAdapter)
    assert registry.exists("sample-adapter")
    adapter_type = registry.resolve_type("sample-adapter")
    assert adapter_type is SampleExecutionAdapter


def test_registry_lifecycle_state() -> None:
    registry = AdapterRegistry()
    registry.register(make_adapter_metadata())
    assert registry.get_state("sample-adapter") == AdapterState.REGISTERED
    registry.set_state("sample-adapter", AdapterState.INITIALIZED)
    assert registry.get_state("sample-adapter") == AdapterState.INITIALIZED


def test_registry_duplicate_raises() -> None:
    registry = AdapterRegistry()
    registry.register(make_adapter_metadata())
    with pytest.raises(AdapterRegistrationError):
        registry.register(make_adapter_metadata())


def test_registry_not_found_raises() -> None:
    registry = AdapterRegistry()
    with pytest.raises(AdapterNotFoundError):
        registry.resolve("missing")


def test_adapter_registry_unregister() -> None:
    registry = AdapterRegistry()
    registry.register(make_adapter_metadata())
    registry.unregister("sample-adapter")
    with pytest.raises(AdapterNotFoundError):
        registry.resolve("sample-adapter")


def test_adapter_registry_get_version() -> None:
    registry = AdapterRegistry()
    registry.register(make_adapter_metadata(version="2.0.0"))
    assert registry.get_version("sample-adapter") == "2.0.0"


def test_singleton_registry() -> None:
    reset_adapter_registry()
    registry = get_adapter_registry()
    registry.register(make_adapter_metadata(adapter_id="singleton"))
    assert get_adapter_registry().list() == ("singleton",)
    reset_adapter_registry()
