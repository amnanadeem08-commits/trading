"""Unit tests for plugin registry."""

from __future__ import annotations

import pytest

from ml_engine_plugins import PluginNotFoundError, PluginRegistry, PluginState
from tests.ml_engine_plugins_helpers import StubMLPlugin


@pytest.mark.unit
def test_plugin_registry_register_and_lookup() -> None:
    registry = PluginRegistry()
    plugin = StubMLPlugin(plugin_id="engine-1")
    record = registry.register(plugin)
    assert record.plugin_id == "engine-1"
    assert record.state == PluginState.REGISTERED
    assert registry.lookup("engine-1").plugin_id == "engine-1"


@pytest.mark.unit
def test_plugin_registry_update_state_and_clear() -> None:
    registry = PluginRegistry()
    registry.register(StubMLPlugin())
    registry.update_state("stub-engine", PluginState.LOADED)
    assert registry.lookup("stub-engine").state == PluginState.LOADED
    registry.clear()
    assert registry.list() == ()


@pytest.mark.unit
def test_plugin_registry_lookup_missing() -> None:
    registry = PluginRegistry()
    with pytest.raises(PluginNotFoundError):
        registry.lookup("missing")
