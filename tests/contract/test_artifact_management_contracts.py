"""Contract tests for artifact management."""

from __future__ import annotations

import inspect

import pytest

from artifact_management import (
    ArtifactCache,
    ArtifactHealthChecker,
    ArtifactLifecycleManager,
    ArtifactMetricsCollector,
    ArtifactReference,
    ArtifactRegistry,
    ArtifactResolver,
    ArtifactValidator,
    ArtifactVersionRegistry,
    FrameworkAdapterArtifactBridge,
    URIResolver,
    build_artifact_bridge,
)


@pytest.mark.contract
def test_artifact_management_public_exports() -> None:
    assert ArtifactReference is not None
    assert FrameworkAdapterArtifactBridge is not None
    assert callable(build_artifact_bridge)


@pytest.mark.contract
def test_artifact_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ArtifactRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods
    assert "list" in methods
    assert "clear" in methods


@pytest.mark.contract
def test_artifact_resolver_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ArtifactResolver, predicate=inspect.isfunction)
    }
    assert "resolve" in methods
    uri_methods = {
        name for name, _ in inspect.getmembers(URIResolver, predicate=inspect.isfunction)
    }
    assert "resolve" in uri_methods


@pytest.mark.contract
def test_artifact_cache_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(ArtifactCache, predicate=inspect.isfunction)}
    assert "put" in methods
    assert "get" in methods
    assert "clear" in methods


@pytest.mark.contract
def test_artifact_framework_components() -> None:
    assert ArtifactValidator is not None
    assert ArtifactLifecycleManager is not None
    assert ArtifactHealthChecker is not None
    assert ArtifactMetricsCollector is not None
    assert ArtifactVersionRegistry is not None
