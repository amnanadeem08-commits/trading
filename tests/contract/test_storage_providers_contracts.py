"""Contract tests for storage providers."""

from __future__ import annotations

import inspect

import pytest

from storage_providers import (
    ArtifactManagementStorageBridge,
    ProviderHealthChecker,
    ProviderLifecycleManager,
    ProviderMetricsCollector,
    ProviderRegistry,
    ProviderResolver,
    ProviderVersionRegistry,
    StorageProvider,
    StorageProviderValidator,
    StubLocalProvider,
    build_storage_bridge,
)


@pytest.mark.contract
def test_storage_providers_public_exports() -> None:
    assert StorageProvider is not None
    assert ArtifactManagementStorageBridge is not None
    assert callable(build_storage_bridge)


@pytest.mark.contract
def test_storage_provider_contract() -> None:
    from storage_providers import LocalStorageProvider

    methods = {
        name for name, _ in inspect.getmembers(StorageProvider, predicate=inspect.isfunction)
    }
    for method in (
        "provider_id",
        "provider_type",
        "metadata",
        "manifest",
        "capabilities",
        "validate",
        "resolve",
        "fetch_metadata",
        "shutdown",
    ):
        assert method in methods
    assert StubLocalProvider().provider_id() == "stub-local-provider"
    assert LocalStorageProvider.__mro__[1].__name__ == "StorageProvider"


@pytest.mark.contract
def test_provider_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ProviderRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods
    assert "resolve" in methods
    assert "clear" in methods


@pytest.mark.contract
def test_provider_resolver_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ProviderResolver, predicate=inspect.isfunction)
    }
    assert "resolve" in methods


@pytest.mark.contract
def test_storage_provider_framework_components() -> None:
    assert StorageProviderValidator is not None
    assert ProviderLifecycleManager is not None
    assert ProviderHealthChecker is not None
    assert ProviderMetricsCollector is not None
    assert ProviderVersionRegistry is not None
