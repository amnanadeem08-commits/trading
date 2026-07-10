"""Helpers for plugin tests."""

from __future__ import annotations

from plugins import (
    ApiVersionConstraint,
    BasePlugin,
    Capability,
    PermissionModel,
    PlatformVersionConstraint,
    Plugin,
    PluginDependency,
    PluginManifest,
    PluginRegistry,
    plugin,
)
from plugins.discovery import make_default_manifest


@plugin(plugin_id="test-plugin", auto_register=True)
class TestPlugin(BasePlugin):
    """Concrete plugin used in unit tests."""

    def plugin_id(self) -> str:
        return "test-plugin"

    def name(self) -> str:
        return "Test Plugin"

    def version(self) -> str:
        return "1.0.0"

    def author(self) -> str:
        return "platform"

    def description(self) -> str:
        return "Test plugin"

    def manifest(self) -> PluginManifest:
        return make_default_manifest()


def make_plugin(
    *,
    plugin_id: str = "test-plugin",
    version: str = "1.0.0",
    dependencies: tuple[PluginDependency, ...] = (),
    capabilities: tuple[Capability, ...] = (),
    permissions: tuple[str, ...] = (),
) -> Plugin:
    manifest = PluginManifest(
        api_version="1.0.0",
        api_version_bounds=ApiVersionConstraint(minimum_api_version="1.0.0"),
        platform_version=PlatformVersionConstraint(minimum="0.1.0", maximum="1.0.0"),
        dependencies=dependencies,
        permissions=PermissionModel(permissions=permissions),
        capabilities=capabilities,
    )
    return Plugin(
        plugin_id=plugin_id,
        name=f"Plugin {plugin_id}",
        version=version,
        author="platform",
        description="Test plugin",
        manifest=manifest,
    )


def make_capability(*, capability_id: str = "cap-1") -> Capability:
    return Capability(
        capability_id=capability_id,
        type="ingest",
        version="1.0.0",
        metadata={"scope": "test"},
    )


def register_plugin(registry: PluginRegistry, plugin_def: Plugin) -> None:
    registry.register(plugin_def)
