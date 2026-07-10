"""Contract tests for framework adapter foundation."""

from __future__ import annotations

import inspect

import pytest

from framework_adapters import (
    AdapterFactory,
    AdapterRegistry,
    AdapterResolver,
    FrameworkAdapter,
    FrameworkAdapterHealthChecker,
    FrameworkAdapterValidator,
    MLEngineAdapterBridge,
    build_adapter_bridge,
)


@pytest.mark.contract
def test_framework_adapter_public_exports() -> None:
    assert FrameworkAdapter is not None
    assert MLEngineAdapterBridge is not None
    assert callable(build_adapter_bridge)


@pytest.mark.contract
def test_framework_adapter_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(FrameworkAdapter, predicate=inspect.isfunction)
    }
    assert "adapter_id" in methods
    assert "engine_type" in methods
    assert "metadata" in methods
    assert "manifest" in methods
    assert "capabilities" in methods
    assert "validate_environment" in methods
    assert "load_artifact" in methods
    assert "create_executor" in methods
    assert "shutdown" in methods


@pytest.mark.contract
def test_adapter_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(AdapterRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods
    assert "list" in methods
    assert "clear" in methods


@pytest.mark.contract
def test_adapter_factory_and_resolver_contract() -> None:
    factory_methods = {
        name for name, _ in inspect.getmembers(AdapterFactory, predicate=inspect.isfunction)
    }
    resolver_methods = {
        name for name, _ in inspect.getmembers(AdapterResolver, predicate=inspect.isfunction)
    }
    assert "create" in factory_methods
    assert "resolve" in resolver_methods


@pytest.mark.contract
def test_framework_adapter_framework_components() -> None:
    assert FrameworkAdapterValidator is not None
    assert FrameworkAdapterHealthChecker is not None
