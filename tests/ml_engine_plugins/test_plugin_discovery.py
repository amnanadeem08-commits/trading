"""Unit tests for plugin discovery."""

from __future__ import annotations

import pytest

from ml_engine_plugins import PluginDiscovery, PluginDiscoveryError
from tests.ml_engine_plugins_helpers import StubMLPlugin


@pytest.mark.unit
def test_plugin_discovery_finds_providers() -> None:
    discovery = PluginDiscovery()
    discovery.register_provider(StubMLPlugin(plugin_id="engine-1"))
    plugins = discovery.discover()
    assert len(plugins) == 1
    assert plugins[0].plugin_id() == "engine-1"


@pytest.mark.unit
def test_plugin_discovery_rejects_empty_id() -> None:
    discovery = PluginDiscovery()

    class BadPlugin(StubMLPlugin):
        def plugin_id(self) -> str:
            return ""

    discovery.register_provider(BadPlugin())
    with pytest.raises(PluginDiscoveryError):
        discovery.discover()
