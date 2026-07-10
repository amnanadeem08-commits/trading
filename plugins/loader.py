"""Plugin loader."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from plugins.discovery import PluginDiscovery, _normalize_manifest_payload, ensure_concrete_plugin
from plugins.exceptions import PluginLoadError
from plugins.manifest import PluginManifest
from plugins.plugin import LoadedPlugin, Plugin
from plugins.registry import PluginRegistry
from plugins.state import PluginState


class PluginLoader:
    """Loads plugin implementations from packages and directories."""

    def __init__(self, discovery: PluginDiscovery | None = None) -> None:
        self._discovery = discovery or PluginDiscovery()

    def load_from_package(self, module_name: str) -> tuple[LoadedPlugin, ...]:
        """Load plugin implementations from a Python module."""
        try:
            module = importlib.import_module(module_name)
        except ImportError as error:
            msg = f"Failed to import plugin module: {module_name}"
            raise PluginLoadError(msg) from error
        loaded: list[LoadedPlugin] = []
        for plugin_type in self._discovery._discover_in_module(module):
            ensure_concrete_plugin(plugin_type)
            implementation = plugin_type()
            definition = implementation.to_definition()
            loaded.append(
                LoadedPlugin(
                    definition=definition,
                    implementation=implementation,
                    state=PluginState.LOADED,
                )
            )
        if not loaded:
            msg = f"No plugins found in module: {module_name}"
            raise PluginLoadError(msg)
        return tuple(loaded)

    def load_from_directory(self, directory: Path) -> tuple[Plugin, ...]:
        """Load plugin definitions from manifest files in a directory."""
        return self._discovery.discover_manifests(directory)

    def discover(
        self,
        *,
        modules: tuple[str, ...] | None = None,
        directory: Path | None = None,
    ) -> tuple[Plugin, ...]:
        """Discover plugin definitions."""
        return self._discovery.discover(modules=modules, directory=directory)

    def load_manifest(self, manifest_path: Path) -> Plugin:
        """Load a single plugin definition from a manifest file."""
        return self._discovery._load_manifest_file(manifest_path)

    def register_discovered(
        self,
        registry: PluginRegistry,
        *,
        modules: tuple[str, ...] | None = None,
        directory: Path | None = None,
    ) -> tuple[str, ...]:
        """Discover and register plugin definitions."""
        registered: list[str] = []
        for plugin in self.discover(modules=modules, directory=directory):
            registry.register(plugin)
            registered.append(plugin.plugin_id)
        return tuple(registered)


def load_plugin_module(module_name: str) -> tuple[LoadedPlugin, ...]:
    """Load plugins from a module using the default loader."""
    return PluginLoader().load_from_package(module_name)


def parse_manifest_file(manifest_path: Path) -> PluginManifest:
    """Parse a manifest file into a PluginManifest."""
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        return PluginManifest.model_validate(_normalize_manifest_payload(raw["manifest"]))
    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
        msg = f"Failed to parse manifest: {manifest_path}"
        raise PluginLoadError(msg) from error
