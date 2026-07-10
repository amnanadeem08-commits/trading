"""Unit tests for plugin registry."""

from __future__ import annotations

import pytest

from plugins import (
    PluginNotFoundError,
    PluginRegistrationError,
    PluginRegistry,
    reset_plugin_registry,
)
from tests.plugin_helpers import make_plugin, register_plugin


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_plugin_registry()
    yield
    reset_plugin_registry()


@pytest.mark.unit
def test_registry_register_and_resolve() -> None:
    registry = PluginRegistry()
    plugin = make_plugin()
    register_plugin(registry, plugin)
    resolved = registry.resolve("test-plugin")
    assert resolved.plugin_id == "test-plugin"


@pytest.mark.unit
def test_registry_exists_and_list() -> None:
    registry = PluginRegistry()
    register_plugin(registry, make_plugin(plugin_id="alpha"))
    register_plugin(registry, make_plugin(plugin_id="beta"))
    assert registry.exists("alpha") is True
    assert registry.list() == ("alpha", "beta")


@pytest.mark.unit
def test_registry_unregister() -> None:
    registry = PluginRegistry()
    register_plugin(registry, make_plugin())
    registry.unregister("test-plugin")
    assert registry.exists("test-plugin") is False


@pytest.mark.unit
def test_registry_duplicate_raises() -> None:
    registry = PluginRegistry()
    plugin = make_plugin()
    register_plugin(registry, plugin)
    with pytest.raises(PluginRegistrationError):
        register_plugin(registry, plugin)


@pytest.mark.unit
def test_registry_resolve_missing_raises() -> None:
    registry = PluginRegistry()
    with pytest.raises(PluginNotFoundError):
        registry.resolve("missing")


@pytest.mark.unit
def test_registry_validate_method() -> None:
    registry = PluginRegistry()
    plugin = make_plugin()
    result = registry.validate(plugin, platform_version="0.1.0", platform_api_version="1.0.0")
    assert result.valid is True
