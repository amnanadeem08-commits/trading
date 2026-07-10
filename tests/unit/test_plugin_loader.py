"""Unit tests for plugin loader and discovery."""

from __future__ import annotations

import json

import pytest

from plugins import PluginLoader, PluginLoadError
from tests.plugin_helpers import TestPlugin


@pytest.mark.unit
def test_loader_discovers_test_plugin_module() -> None:
    loader = PluginLoader()
    plugins = loader.discover(modules=("tests.plugin_helpers",))
    assert any(plugin.plugin_id == "test-plugin" for plugin in plugins)


@pytest.mark.unit
def test_loader_load_from_package() -> None:
    loader = PluginLoader()
    loaded = loader.load_from_package("tests.plugin_helpers")
    assert len(loaded) == 1
    assert loaded[0].definition.plugin_id == "test-plugin"
    assert isinstance(loaded[0].implementation, TestPlugin)


@pytest.mark.unit
def test_loader_load_from_directory(tmp_path) -> None:
    plugin_dir = tmp_path / "sample-plugin"
    plugin_dir.mkdir()
    manifest = {
        "plugin_id": "dir-plugin",
        "name": "Directory Plugin",
        "version": "1.0.0",
        "author": "platform",
        "description": "from directory",
        "manifest": {
            "api_version": "1.0.0",
            "api_version_bounds": {"minimum_api_version": "1.0.0"},
            "platform_version": {"minimum": "0.1.0"},
            "dependencies": [],
            "permissions": {"permissions": []},
            "capabilities": [],
        },
    }
    (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    loader = PluginLoader()
    plugins = loader.load_from_directory(tmp_path)
    assert len(plugins) == 1
    assert plugins[0].plugin_id == "dir-plugin"


@pytest.mark.unit
def test_loader_invalid_directory_raises(tmp_path) -> None:
    loader = PluginLoader()
    with pytest.raises(PluginLoadError):
        loader.load_from_directory(tmp_path / "missing")


@pytest.mark.unit
def test_discovery_register_discovered() -> None:
    from plugins import PluginRegistry

    registry = PluginRegistry()
    loader = PluginLoader()
    registered = loader.register_discovered(registry, modules=("tests.plugin_helpers",))
    assert registered == ("test-plugin",)
    assert registry.exists("test-plugin")


@pytest.mark.unit
def test_loader_invalid_manifest_raises(tmp_path) -> None:
    plugin_dir = tmp_path / "bad-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "manifest.json").write_text("not-json", encoding="utf-8")
    loader = PluginLoader()
    with pytest.raises(PluginLoadError):
        loader.load_manifest(plugin_dir / "manifest.json")


@pytest.mark.unit
def test_ensure_concrete_plugin_rejects_abstract() -> None:
    from abc import ABC, abstractmethod

    from plugins import BasePlugin, ensure_concrete_plugin
    from plugins.exceptions import PluginLoadError

    class AbstractPlugin(BasePlugin, ABC):
        @abstractmethod
        def plugin_id(self) -> str: ...

        @abstractmethod
        def name(self) -> str: ...

        @abstractmethod
        def version(self) -> str: ...

        @abstractmethod
        def author(self) -> str: ...

        @abstractmethod
        def description(self) -> str: ...

        @abstractmethod
        def manifest(self): ...

    with pytest.raises(PluginLoadError):
        ensure_concrete_plugin(AbstractPlugin)


@pytest.mark.unit
def test_loader_empty_module_raises() -> None:
    loader = PluginLoader()
    with pytest.raises(PluginLoadError):
        loader.load_from_package("plugins.exceptions")
