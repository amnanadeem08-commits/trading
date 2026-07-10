"""Plugin discovery."""

from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
from pathlib import Path
from types import ModuleType

from pydantic import ValidationError

from plugins.decorators import plugin_metadata
from plugins.exceptions import PluginLoadError
from plugins.manifest import ApiVersionConstraint, PlatformVersionConstraint, PluginManifest
from plugins.plugin import BasePlugin, Plugin
from plugins.sandbox import PermissionModel


class PluginDiscovery:
    """Discovers plugin classes and manifest files."""

    def __init__(self, package_name: str = "plugins") -> None:
        self._package_name = package_name

    def discover_modules(self, modules: tuple[str, ...] | None = None) -> tuple[str, ...]:
        """Discover importable module names including nested packages."""
        if modules is not None:
            return modules
        package = importlib.import_module(self._package_name)
        if not hasattr(package, "__path__"):
            return (self._package_name,)
        names: list[str] = []
        package_paths = package.__path__
        for module_info in pkgutil.walk_packages(package_paths, prefix=f"{self._package_name}."):
            if module_info.name.endswith(".tests"):
                continue
            names.append(module_info.name)
        if not names:
            for module_path in sorted(Path(str(package_paths[0])).glob("*.py")):
                if module_path.name.startswith("_"):
                    continue
                names.append(f"{self._package_name}.{module_path.stem}")
        return tuple(sorted(names))

    def discover_classes(
        self,
        modules: tuple[str, ...] | None = None,
    ) -> tuple[type[BasePlugin], ...]:
        """Discover concrete plugin classes from modules."""
        discovered: list[type[BasePlugin]] = []
        for module_name in self.discover_modules(modules):
            try:
                module = importlib.import_module(module_name)
            except ImportError as error:
                msg = f"Failed to import plugin module: {module_name}"
                raise PluginLoadError(msg) from error
            discovered.extend(self._discover_in_module(module))
        return tuple(discovered)

    def discover_manifests(self, directory: Path) -> tuple[Plugin, ...]:
        """Discover plugin definitions from manifest files in a directory."""
        if not directory.is_dir():
            msg = f"Plugin directory not found: {directory}"
            raise PluginLoadError(msg)
        plugins: list[Plugin] = []
        for manifest_path in sorted(directory.glob("*/manifest.json")):
            plugins.append(self._load_manifest_file(manifest_path))
        return tuple(plugins)

    def discover(
        self,
        *,
        modules: tuple[str, ...] | None = None,
        directory: Path | None = None,
    ) -> tuple[Plugin, ...]:
        """Discover plugins from modules and optional manifest directory."""
        discovered: list[Plugin] = []
        seen_ids: set[str] = set()
        for plugin_type in self.discover_classes(modules):
            instance = plugin_type()
            definition = instance.to_definition()
            if definition.plugin_id in seen_ids:
                continue
            seen_ids.add(definition.plugin_id)
            discovered.append(definition)
        if directory is not None:
            for plugin in self.discover_manifests(directory):
                if plugin.plugin_id in seen_ids:
                    continue
                seen_ids.add(plugin.plugin_id)
                discovered.append(plugin)
        return tuple(discovered)

    def _discover_in_module(self, module: ModuleType) -> tuple[type[BasePlugin], ...]:
        discovered: list[type[BasePlugin]] = []
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__:
                continue
            if not issubclass(obj, BasePlugin) or obj is BasePlugin:
                continue
            if inspect.isabstract(obj):
                continue
            discovered.append(obj)
        return tuple(discovered)

    def _load_manifest_file(self, manifest_path: Path) -> Plugin:
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            msg = f"Failed to read plugin manifest: {manifest_path}"
            raise PluginLoadError(msg) from error
        try:
            manifest = PluginManifest.model_validate(_normalize_manifest_payload(raw["manifest"]))
            return Plugin(
                plugin_id=raw["plugin_id"],
                name=raw["name"],
                version=raw["version"],
                author=raw["author"],
                description=raw.get("description", ""),
                manifest=manifest,
            )
        except (KeyError, ValueError, TypeError, ValidationError) as error:
            msg = f"Invalid plugin manifest schema: {manifest_path}"
            raise PluginLoadError(msg) from error


def discover_plugins(
    *,
    modules: tuple[str, ...] | None = None,
    directory: Path | None = None,
) -> tuple[Plugin, ...]:
    """Discover plugins using the default discovery configuration."""
    return PluginDiscovery().discover(modules=modules, directory=directory)


def ensure_concrete_plugin(plugin_type: type[BasePlugin]) -> None:
    """Validate that a discovered plugin can be instantiated."""
    if inspect.isabstract(plugin_type):
        msg = f"Cannot instantiate abstract plugin: {plugin_type.__name__}"
        raise PluginLoadError(msg)
    metadata = plugin_metadata(plugin_type)
    if metadata.get("plugin_id") is None:
        msg = f"Plugin metadata missing plugin_id: {plugin_type.__name__}"
        raise PluginLoadError(msg)


def make_default_manifest() -> PluginManifest:
    """Return a minimal valid manifest for test plugins."""
    return PluginManifest(
        api_version="1.0.0",
        api_version_bounds=ApiVersionConstraint(minimum_api_version="1.0.0"),
        platform_version=PlatformVersionConstraint(minimum="0.1.0", maximum=None),
        dependencies=(),
        permissions=PermissionModel(permissions=()),
        capabilities=(),
    )


def _normalize_manifest_payload(raw: dict[str, object]) -> dict[str, object]:
    """Normalize JSON manifest payloads for strict tuple fields."""
    normalized = dict(raw)
    dependencies = normalized.get("dependencies")
    if isinstance(dependencies, list):
        normalized["dependencies"] = tuple(dependencies)
    capabilities = normalized.get("capabilities")
    if isinstance(capabilities, list):
        normalized["capabilities"] = tuple(capabilities)
    permissions = normalized.get("permissions")
    if isinstance(permissions, dict):
        permission_values = permissions.get("permissions")
        if isinstance(permission_values, list):
            normalized["permissions"] = {
                **permissions,
                "permissions": tuple(permission_values),
            }
    api_bounds = normalized.get("api_version_bounds")
    if isinstance(api_bounds, dict):
        minimum = api_bounds.get("minimum_api_version") or api_bounds.get("minimum")
        maximum = api_bounds.get("maximum_api_version") or api_bounds.get("maximum")
        if minimum is not None:
            normalized["api_version_bounds"] = {
                "minimum_api_version": minimum,
                "maximum_api_version": maximum,
            }
    elif "api_version" in normalized and "api_version_bounds" not in normalized:
        api_version = normalized["api_version"]
        if isinstance(api_version, str):
            normalized["api_version_bounds"] = {
                "minimum_api_version": api_version,
                "maximum_api_version": None,
            }
    return normalized
