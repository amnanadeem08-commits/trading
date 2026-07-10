"""Contract tests for ML engine plugin framework."""

from __future__ import annotations

import inspect

import pytest

from ml_engine_plugins import (
    MLPlugin,
    MLRuntimePluginBridge,
    PluginDiscovery,
    PluginHealthChecker,
    PluginHealthResult,
    PluginLifecycleManager,
    PluginLoader,
    PluginManifest,
    PluginMetadata,
    PluginMetricsCollector,
    PluginRegistry,
    PluginValidator,
    PluginVersionRegistry,
    build_plugin_bridge,
)


@pytest.mark.contract
def test_ml_engine_plugin_public_exports() -> None:
    assert MLPlugin is not None
    assert MLRuntimePluginBridge is not None
    assert callable(build_plugin_bridge)


@pytest.mark.contract
def test_ml_plugin_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(MLPlugin, predicate=inspect.isfunction)}
    assert "plugin_id" in methods
    assert "metadata" in methods
    assert "manifest" in methods
    assert "capabilities" in methods
    assert "create_executor" in methods


@pytest.mark.contract
def test_plugin_registry_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(PluginRegistry, predicate=inspect.isfunction)}
    assert "register" in methods
    assert "lookup" in methods
    assert "list" in methods
    assert "clear" in methods


@pytest.mark.contract
def test_plugin_loader_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(PluginLoader, predicate=inspect.isfunction)}
    assert "load" in methods
    assert "unload" in methods


@pytest.mark.contract
def test_plugin_framework_components() -> None:
    assert PluginDiscovery is not None
    assert PluginValidator is not None
    assert PluginLifecycleManager is not None
    assert PluginHealthChecker is not None
    assert PluginMetricsCollector is not None
    assert PluginVersionRegistry is not None
    assert PluginMetadata is not None
    assert PluginManifest is not None
    assert PluginHealthResult is not None
