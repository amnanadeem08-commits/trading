"""Plugin validation."""

from __future__ import annotations

from dataclasses import dataclass

from plugins.compatibility import check_manifest_compatibility
from plugins.dependency import build_dependency_graph, detect_cycle, topological_order
from plugins.exceptions import CircularPluginDependencyError, PermissionConflictError
from plugins.manifest import PluginManifest
from plugins.plugin import Plugin


@dataclass(frozen=True)
class PluginValidationResult:
    """Outcome of plugin validation."""

    valid: bool
    errors: tuple[str, ...] = ()
    load_order: tuple[str, ...] = ()


def _plugins_by_id(plugins: tuple[Plugin, ...]) -> dict[str, Plugin]:
    return {plugin.plugin_id: plugin for plugin in plugins}


def _capability_ids(manifest: PluginManifest) -> tuple[str, ...]:
    return tuple(capability.capability_id for capability in manifest.capabilities)


def _dependency_map(plugins: dict[str, Plugin]) -> dict[str, tuple[str, ...]]:
    dependencies: dict[str, tuple[str, ...]] = {}
    for plugin_id, plugin in plugins.items():
        deps = tuple(dep.plugin_id for dep in plugin.manifest.dependencies)
        dependencies[plugin_id] = deps
    return dependencies


def _detect_permission_conflicts(plugins: tuple[Plugin, ...]) -> tuple[str, ...]:
    exclusive_permissions = {"admin", "filesystem.write", "network.unrestricted"}
    conflicts: list[str] = []
    permission_holders: dict[str, list[str]] = {}
    for plugin in plugins:
        for permission in plugin.manifest.permissions.permissions:
            permission_holders.setdefault(permission, []).append(plugin.plugin_id)
    for permission, holders in sorted(permission_holders.items()):
        if permission in exclusive_permissions and len(holders) > 1:
            conflicts.append(
                f"Permission conflict for '{permission}' between plugins: {', '.join(holders)}",
            )
    return tuple(conflicts)


def _detect_capability_conflicts(plugins: tuple[Plugin, ...]) -> tuple[str, ...]:
    conflicts: list[str] = []
    declared_conflicts: dict[str, set[str]] = {}
    for plugin in plugins:
        for capability in plugin.manifest.capabilities:
            for conflict_id in capability.relations.conflicts:
                declared_conflicts.setdefault(conflict_id, set()).add(plugin.plugin_id)
    for conflict_id, holders in sorted(declared_conflicts.items()):
        if len(holders) > 1:
            holders_label = ", ".join(sorted(holders))
            conflicts.append(
                f"Capability conflict '{conflict_id}' declared by plugins: {holders_label}",
            )
    return tuple(conflicts)


def validate_manifest_schema(manifest: PluginManifest) -> PluginValidationResult:
    """Validate manifest schema constraints."""
    errors: list[str] = []
    capability_ids = _capability_ids(manifest)
    if len(capability_ids) != len(set(capability_ids)):
        errors.append("Duplicate capability identifiers in manifest")
    if not manifest.api_version.strip():
        errors.append("Manifest api_version must not be empty")
    return PluginValidationResult(valid=not errors, errors=tuple(errors))


def validate_plugin_set(
    plugins: tuple[Plugin, ...],
    *,
    platform_version: str,
    platform_api_version: str,
    installed_versions: dict[str, str] | None = None,
) -> PluginValidationResult:
    """Validate a set of plugins for registration."""
    errors: list[str] = []
    plugin_map = _plugins_by_id(plugins)
    plugin_ids = [plugin.plugin_id for plugin in plugins]
    if len(plugin_ids) != len(set(plugin_ids)):
        errors.append("Duplicate plugin identifiers detected")

    all_capability_ids: list[str] = []
    for plugin in plugins:
        manifest_result = validate_manifest_schema(plugin.manifest)
        errors.extend(manifest_result.errors)
        all_capability_ids.extend(_capability_ids(plugin.manifest))
        for dependency in plugin.manifest.dependencies:
            if dependency.plugin_id == plugin.plugin_id:
                errors.append(f"Plugin depends on itself: {plugin.plugin_id}")
            elif dependency.plugin_id not in plugin_map:
                errors.append(
                    f"Missing dependency '{dependency.plugin_id}' required by '{plugin.plugin_id}'",
                )
        compatibility = check_manifest_compatibility(
            plugin.manifest,
            platform_version=platform_version,
            platform_api_version=platform_api_version,
            installed_versions=installed_versions or {},
        )
        errors.extend(compatibility.errors)

    if len(all_capability_ids) != len(set(all_capability_ids)):
        errors.append("Duplicate capability identifiers across plugins")

    errors.extend(_detect_capability_conflicts(plugins))

    permission_conflicts = _detect_permission_conflicts(plugins)
    if permission_conflicts:
        raise PermissionConflictError(
            "Plugin permission conflicts detected",
            conflicts=permission_conflicts,
        )

    if errors:
        return PluginValidationResult(valid=False, errors=tuple(errors))

    graph = build_dependency_graph(tuple(plugin_map.keys()), _dependency_map(plugin_map))
    cycle = detect_cycle(graph)
    if cycle is not None:
        raise CircularPluginDependencyError(cycle)

    return PluginValidationResult(
        valid=True,
        load_order=topological_order(graph),
    )


def validate_plugin(
    plugin: Plugin,
    *,
    platform_version: str,
    platform_api_version: str,
    installed_versions: dict[str, str] | None = None,
    registered_plugins: tuple[Plugin, ...] = (),
) -> PluginValidationResult:
    """Validate a single plugin against registered plugins."""
    combined = (*registered_plugins, plugin)
    return validate_plugin_set(
        combined,
        platform_version=platform_version,
        platform_api_version=platform_api_version,
        installed_versions=installed_versions,
    )
