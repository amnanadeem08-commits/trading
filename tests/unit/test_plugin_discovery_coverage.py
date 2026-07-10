"""Extended discovery coverage tests."""

from __future__ import annotations

import json
import sys
import types
from abc import ABC, abstractmethod

import pytest

from plugins import BasePlugin, PluginDiscovery, PluginLoadError, discover_plugins
from plugins.discovery import (
    _normalize_manifest_payload,
    ensure_concrete_plugin,
    make_default_manifest,
)
from plugins.manifest import PluginManifest
from tests.plugin_helpers import TestPlugin


@pytest.mark.unit
def test_discover_modules_includes_nested_package(tmp_path, monkeypatch) -> None:
    package_root = tmp_path / "sample_plugins"
    package_root.mkdir()
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    nested = package_root / "nested"
    nested.mkdir()
    (nested / "__init__.py").write_text("", encoding="utf-8")
    (nested / "plugin_impl.py").write_text(
        "from tests.plugin_helpers import TestPlugin\n",
        encoding="utf-8",
    )
    sys.path.insert(0, str(tmp_path))
    module = types.ModuleType("sample_plugins")
    module.__path__ = [str(package_root)]  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sample_plugins", module)
    discovery = PluginDiscovery(package_name="sample_plugins")
    modules = discovery.discover_modules()
    assert "sample_plugins.nested.plugin_impl" in modules


@pytest.mark.unit
def test_discover_deduplicates_plugin_ids() -> None:
    discovery = PluginDiscovery()
    plugins = discovery.discover(modules=("tests.plugin_helpers", "tests.plugin_helpers"))
    plugin_ids = [plugin.plugin_id for plugin in plugins]
    assert plugin_ids.count("test-plugin") == 1


@pytest.mark.unit
def test_discover_manifest_invalid_schema_raises(tmp_path) -> None:
    plugin_dir = tmp_path / "bad"
    plugin_dir.mkdir()
    (plugin_dir / "manifest.json").write_text('{"plugin_id": "x"}', encoding="utf-8")
    discovery = PluginDiscovery()
    with pytest.raises(PluginLoadError):
        discovery.discover_manifests(tmp_path)


@pytest.mark.unit
def test_discover_manifest_malformed_json_raises(tmp_path) -> None:
    plugin_dir = tmp_path / "bad"
    plugin_dir.mkdir()
    (plugin_dir / "manifest.json").write_text("{bad", encoding="utf-8")
    discovery = PluginDiscovery()
    with pytest.raises(PluginLoadError):
        discovery.discover_manifests(tmp_path)


@pytest.mark.unit
def test_discover_classes_import_failure_raises(monkeypatch) -> None:
    discovery = PluginDiscovery()

    def _fail_import(_name: str):
        raise ImportError("missing")

    monkeypatch.setattr("plugins.discovery.importlib.import_module", _fail_import)
    with pytest.raises(PluginLoadError):
        discovery.discover_classes(modules=("missing.module",))


@pytest.mark.unit
def test_discover_empty_package_returns_module_name(monkeypatch) -> None:
    module = types.ModuleType("empty_plugins")
    monkeypatch.setitem(sys.modules, "empty_plugins", module)
    discovery = PluginDiscovery(package_name="empty_plugins")
    assert discovery.discover_modules() == ("empty_plugins",)


@pytest.mark.unit
def test_normalize_manifest_payload_converts_lists() -> None:
    normalized = _normalize_manifest_payload(
        {
            "api_version": "1.0.0",
            "dependencies": [],
            "capabilities": [],
            "permissions": {"permissions": []},
            "platform_version": {"minimum": "0.1.0"},
        },
    )
    assert normalized["dependencies"] == ()
    assert normalized["capabilities"] == ()
    assert normalized["api_version_bounds"]["minimum_api_version"] == "1.0.0"


@pytest.mark.unit
def test_discover_plugins_helper_returns_test_plugin() -> None:
    plugins = discover_plugins(modules=("tests.plugin_helpers",))
    assert any(plugin.plugin_id == TestPlugin().plugin_id() for plugin in plugins)


@pytest.mark.unit
def test_manifest_conflict_directory_skips_duplicate(tmp_path) -> None:
    for name in ("a", "b"):
        plugin_dir = tmp_path / name
        plugin_dir.mkdir()
        manifest = {
            "plugin_id": "same-id",
            "name": "Dup",
            "version": "1.0.0",
            "author": "platform",
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
    discovery = PluginDiscovery()
    plugins = discovery.discover(directory=tmp_path)
    assert len(plugins) == 1


@pytest.mark.unit
def test_discover_manifests_directory_not_found(tmp_path) -> None:
    discovery = PluginDiscovery()
    missing = tmp_path / "missing"
    with pytest.raises(PluginLoadError, match="Plugin directory not found"):
        discovery.discover_manifests(missing)


@pytest.mark.unit
def test_discover_modules_skips_tests_suffix(tmp_path, monkeypatch) -> None:
    package_root = tmp_path / "pkg"
    package_root.mkdir()
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    tests_pkg = package_root / "nested.tests"
    tests_pkg.mkdir()
    (tests_pkg / "__init__.py").write_text("", encoding="utf-8")
    (tests_pkg / "plugin_impl.py").write_text("", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    module = types.ModuleType("pkg")
    module.__path__ = [str(package_root)]  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pkg", module)
    discovery = PluginDiscovery(package_name="pkg")
    modules = discovery.discover_modules()
    assert "pkg.nested.tests.plugin_impl" not in modules


@pytest.mark.unit
def test_discover_modules_glob_fallback_when_walk_packages_empty(tmp_path, monkeypatch) -> None:
    package_root = tmp_path / "flat_plugins"
    package_root.mkdir()
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "alpha.py").write_text("", encoding="utf-8")
    (package_root / "_private.py").write_text("", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    module = types.ModuleType("flat_plugins")
    module.__path__ = [str(package_root)]  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "flat_plugins", module)
    monkeypatch.setattr(
        "plugins.discovery.pkgutil.walk_packages", lambda *_args, **_kwargs: iter(())
    )
    discovery = PluginDiscovery(package_name="flat_plugins")
    assert discovery.discover_modules() == ("flat_plugins.alpha",)


@pytest.mark.unit
def test_discover_in_module_skips_abstract_classes() -> None:
    class AbstractPlugin(BasePlugin, ABC):
        @abstractmethod
        def plugin_id(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def name(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def version(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def author(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def description(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def manifest(self) -> PluginManifest:
            raise NotImplementedError

    class ConcretePlugin(BasePlugin):
        def plugin_id(self) -> str:
            return "concrete-plugin"

        def name(self) -> str:
            return "Concrete"

        def version(self) -> str:
            return "1.0.0"

        def author(self) -> str:
            return "platform"

        def description(self) -> str:
            return "concrete"

        def manifest(self) -> PluginManifest:
            return make_default_manifest()

    module = types.ModuleType("abstract_module")
    AbstractPlugin.__module__ = "abstract_module"
    ConcretePlugin.__module__ = "abstract_module"
    module.AbstractPlugin = AbstractPlugin
    module.ConcretePlugin = ConcretePlugin
    discovery = PluginDiscovery()
    discovered = discovery._discover_in_module(module)
    assert discovered == (ConcretePlugin,)


@pytest.mark.unit
def test_ensure_concrete_plugin_rejects_abstract() -> None:
    class AbstractPlugin(BasePlugin, ABC):
        @abstractmethod
        def plugin_id(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def name(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def version(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def author(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def description(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def manifest(self) -> PluginManifest:
            raise NotImplementedError

    with pytest.raises(PluginLoadError, match="abstract plugin"):
        ensure_concrete_plugin(AbstractPlugin)


@pytest.mark.unit
def test_ensure_concrete_plugin_requires_plugin_id() -> None:
    class MissingMetadataPlugin(BasePlugin):
        def plugin_id(self) -> str:
            return "missing-metadata"

        def name(self) -> str:
            return "Missing Metadata"

        def version(self) -> str:
            return "1.0.0"

        def author(self) -> str:
            return "platform"

        def description(self) -> str:
            return "missing metadata"

        def manifest(self) -> PluginManifest:
            return make_default_manifest()

    with pytest.raises(PluginLoadError, match="missing plugin_id"):
        ensure_concrete_plugin(MissingMetadataPlugin)


@pytest.mark.unit
def test_normalize_manifest_payload_api_bounds_aliases() -> None:
    normalized = _normalize_manifest_payload(
        {
            "api_version": "1.0.0",
            "api_version_bounds": {"minimum": "1.0.0", "maximum": "2.0.0"},
            "platform_version": {"minimum": "0.1.0"},
            "dependencies": [],
            "permissions": {"permissions": []},
            "capabilities": [],
        },
    )
    assert normalized["api_version_bounds"] == {
        "minimum_api_version": "1.0.0",
        "maximum_api_version": "2.0.0",
    }
