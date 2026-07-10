# Plugin Architecture

## Overview

The `plugins/` package provides a generic extension framework for registering, validating, loading, enabling, and unloading platform capabilities without modifying core code. It is an orchestration-layer package alongside `pipeline/` and `workflow/`.

```
Plugin Definition (Plugin)
    ↓
Manifest (PluginManifest)
    ↓
Discovery (PluginDiscovery)
    ↓
Registration (PluginRegistry)
    ↓
Validation (validate_plugin_set)
    ↓
Loading (PluginLoader / PluginManager)
    ↓
Lifecycle (PluginLifecycle)
    ↓
Execution coordination (PluginManager)
```

## Core Contracts

| Contract | Purpose |
|---|---|
| `Plugin` | Registered plugin definition (id, name, version, author, manifest) |
| `BasePlugin` | Executable plugin implementation ABC |
| `PluginManifest` | API bounds, platform bounds, dependencies, permissions, capabilities |
| `Capability` | Capability with `CapabilityRelations` (provides, requires, optional, conflicts) |
| `PluginState` | Lifecycle states: discovered → loaded → initialized → enabled → disabled/stopped/failed |

## Discovery Flow

1. `PluginDiscovery.discover_modules()` walks packages with `pkgutil.walk_packages`, including nested packages.
2. `discover_classes()` imports modules and finds concrete `BasePlugin` subclasses.
3. `discover_manifests()` reads `*/manifest.json` from a directory.
4. `discover()` merges class-based and manifest-based definitions, deduplicating by `plugin_id`.
5. Malformed manifests and import failures raise `PluginLoadError`.

## Registry

`PluginRegistry` is thread-safe and supports:

- `register()`, `unregister()`, `resolve()`, `exists()`, `list()`, `all()`, `validate()`

Process-wide singleton: `get_plugin_registry()` / `reset_plugin_registry()`.

## Loader

`PluginLoader` loads plugins from:

- Python modules (`load_from_package()`)
- Manifest directories (`load_from_directory()`)
- Combined discovery (`discover()`, `register_discovered()`)

## Lifecycle

`PluginLifecycle` manages per-plugin transitions:

- `initialize()` — loaded/stopped → initialized
- `start()` — initialized/disabled → enabled
- `stop()` — enabled/initialized → stopped
- `dispose()` — → disabled

`PluginLifecycleManager` publishes events to the existing `EventBus` using `EventType.VALIDATION_COMPLETED` with `source: "plugin"`.

### Lifecycle Events

| Event | When |
|---|---|
| `plugin_discovered` | Discovery completes |
| `plugin_loaded` | Plugin registered in manager |
| `plugin_enabled` | Plugin started |
| `plugin_disabled` | Plugin stopped and disposed |
| `plugin_failed` | Validation or load failure |

## Manager

`PluginManager` coordinates the full runtime:

- `discover()` → `load()` → `enable()` → `disable()` → `unload()`
- `reload()` unloads and reloads a plugin
- Validation runs before registration (duplicates, dependencies, compatibility, permissions)
- Observability registration on enable: health component, metrics gauge, EventBus subscription
- Resource cleanup on unload: health unregister, EventBus unsubscribe, lifecycle handler removal, metrics reset

Singleton: `get_plugin_manager()` / `reset_plugin_manager()`.

## Compatibility Checking

Semantic version utilities in `plugins/compatibility.py`:

| Check | Input |
|---|---|
| API compatibility | `api_version_bounds.minimum_api_version`, `maximum_api_version` |
| Platform compatibility | `platform_version.minimum`, `maximum` |
| Dependency compatibility | `PluginDependency.version_minimum`, `version_maximum` |
| Manifest compatibility | Combined platform + API + dependency checks |

Validation only. No package installation.

## Dependency Validation

`plugins/validation.py` validates:

- Duplicate plugin and capability identifiers
- Missing and self-references in dependency graph
- Dependency cycles (raises `CircularPluginDependencyError`)
- Topological load order
- Permission conflicts (exclusive permissions)
- Capability relation conflicts

## Sandbox Model

Interface only. No runtime isolation.

| Policy | Purpose |
|---|---|
| `ResourceLimits` | CPU and memory limits |
| `PermissionModel` | Permission grants |
| `FilesystemAccessPolicy` | Allowed paths, read-only flag |
| `NetworkAccessPolicy` | Allowed hosts, outbound-only flag |
| `EnvironmentAccessPolicy` | Allowed environment variables |
| `SecretsAccessPolicy` | Allowed secret keys |

`PluginSandbox` ABC exposes all policies. `DefaultPluginSandbox` provides manifest-derived defaults.

## Event Flow

```
PluginManager / PluginLifecycleManager
    ↓ emit()
PluginLifecycleEvent (local handlers)
    ↓ _publish_to_event_bus()
DomainEvent (EventType.VALIDATION_COMPLETED)
    ↓
EventBus.publish() → persistence + subscribers
```

Infrastructure identifiers: `market_id="platform"`, `symbol_id=plugin_id`.

## Public Contracts

All public symbols are exported from `plugins/__init__.py`. Key entry points:

- `PluginManager`, `PluginRegistry`, `PluginLoader`, `PluginDiscovery`
- `validate_plugin()`, `validate_plugin_set()`
- `@plugin`, `plugin_metadata()`
- `PluginSandbox`, `DefaultPluginSandbox`

## Extension Points

| Extension | How |
|---|---|
| Custom plugins | Subclass `BasePlugin`, attach `@plugin` metadata |
| Manifest plugins | Drop `manifest.json` in a plugin directory |
| Sandbox policies | Subclass `PluginSandbox` or configure `DefaultPluginSandbox` |
| Lifecycle handlers | `PluginLifecycleManager.on_event()` |
| Capability relations | Declare `provides`, `requires`, `optional`, `conflicts` on `Capability` |

## Future Persistent Registry Strategy

The current `PluginRegistry` is in-memory and process-local. A future persistent registry would:

1. Implement a `PluginStore` ABC (not yet defined) backed by a database or filesystem catalog.
2. Keep `PluginRegistry` as the hot in-memory cache over `PluginStore`.
3. Preserve validation and compatibility checks at load time.
4. Use `PluginManager.load()` unchanged as the coordination entry point.
5. Add startup `discover()` from persistent catalog plus optional filesystem scan.

No persistent store is implemented in this phase.

## Architecture Boundaries

`plugins/` must not import: `connectors`, `ml`, `ai`, `llm`, `risk`, `execution`, `api`, `dashboard`.

Enforced by `plugins_boundary` rule (R3) and import-linter contract.
