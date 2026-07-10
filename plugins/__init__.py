"""Plugin and extension framework."""

from plugins.capability import Capability, CapabilityRelations
from plugins.compatibility import (
    CompatibilityResult,
    check_api_compatibility,
    check_dependency_compatibility,
    check_manifest_compatibility,
    check_platform_compatibility,
    compare_versions,
    parse_version,
    satisfies,
)
from plugins.decorators import plugin, plugin_metadata
from plugins.dependency import (
    DependencyGraph,
    PluginDependency,
    build_dependency_graph,
    detect_cycle,
    topological_order,
)
from plugins.discovery import PluginDiscovery, discover_plugins, ensure_concrete_plugin
from plugins.exceptions import (
    CircularPluginDependencyError,
    PermissionConflictError,
    PluginCompatibilityError,
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
    PluginRegistrationError,
    PluginStateError,
    PluginValidationError,
)
from plugins.lifecycle import (
    PluginLifecycle,
    PluginLifecycleEvent,
    PluginLifecycleEventType,
    PluginLifecycleManager,
)
from plugins.loader import PluginLoader, load_plugin_module, parse_manifest_file
from plugins.manager import (
    PluginManager,
    PluginResourceHandles,
    get_plugin_manager,
    reset_plugin_manager,
)
from plugins.manifest import ApiVersionConstraint, PlatformVersionConstraint, PluginManifest
from plugins.plugin import BasePlugin, LoadedPlugin, Plugin
from plugins.registry import PluginRegistry, get_plugin_registry, reset_plugin_registry
from plugins.sandbox import (
    DefaultPluginSandbox,
    EnvironmentAccessPolicy,
    FilesystemAccessPolicy,
    NetworkAccessPolicy,
    PermissionModel,
    PluginSandbox,
    ResourceLimits,
    SecretsAccessPolicy,
)
from plugins.state import TERMINAL_PLUGIN_STATES, PluginState
from plugins.validation import (
    PluginValidationResult,
    validate_manifest_schema,
    validate_plugin,
    validate_plugin_set,
)

__all__ = [
    "TERMINAL_PLUGIN_STATES",
    "ApiVersionConstraint",
    "BasePlugin",
    "Capability",
    "CapabilityRelations",
    "CircularPluginDependencyError",
    "CompatibilityResult",
    "DefaultPluginSandbox",
    "DependencyGraph",
    "EnvironmentAccessPolicy",
    "FilesystemAccessPolicy",
    "LoadedPlugin",
    "NetworkAccessPolicy",
    "PermissionConflictError",
    "PermissionModel",
    "PlatformVersionConstraint",
    "Plugin",
    "PluginCompatibilityError",
    "PluginDependency",
    "PluginDiscovery",
    "PluginError",
    "PluginLifecycle",
    "PluginLifecycleEvent",
    "PluginLifecycleEventType",
    "PluginLifecycleManager",
    "PluginLoadError",
    "PluginLoader",
    "PluginManager",
    "PluginManifest",
    "PluginNotFoundError",
    "PluginRegistrationError",
    "PluginRegistry",
    "PluginResourceHandles",
    "PluginSandbox",
    "PluginState",
    "PluginStateError",
    "PluginValidationError",
    "PluginValidationResult",
    "ResourceLimits",
    "SecretsAccessPolicy",
    "build_dependency_graph",
    "check_api_compatibility",
    "check_dependency_compatibility",
    "check_manifest_compatibility",
    "check_platform_compatibility",
    "compare_versions",
    "detect_cycle",
    "discover_plugins",
    "ensure_concrete_plugin",
    "get_plugin_manager",
    "get_plugin_registry",
    "load_plugin_module",
    "parse_manifest_file",
    "parse_version",
    "plugin",
    "plugin_metadata",
    "reset_plugin_manager",
    "reset_plugin_registry",
    "satisfies",
    "topological_order",
    "validate_manifest_schema",
    "validate_plugin",
    "validate_plugin_set",
]
