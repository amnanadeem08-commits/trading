"""Unit tests for plugin loader."""

from __future__ import annotations

import pytest

from ml_engine_plugins import PluginLoader, PluginRegistry, PluginState
from tests.ml_engine_plugins_helpers import StubMLPlugin


@pytest.mark.unit
def test_plugin_loader_loads_plugin() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry=registry)
    record = loader.load(StubMLPlugin())
    assert record.state == PluginState.LOADED


@pytest.mark.unit
def test_plugin_loader_unloads_plugin() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry=registry)
    loader.load(StubMLPlugin())
    loader.unload("stub-engine")
    assert registry.lookup("stub-engine").state == PluginState.UNLOADED
