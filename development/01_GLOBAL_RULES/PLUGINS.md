# Plugin Architecture

## Packages

- `plugins/` — generic plugin discovery, loading, sandbox, lifecycle
- `ml_engine_plugins/` — ML engine plugin pack (stub engine present)
- Connector plugins under `connectors/` for market venues

## Rules

1. Plugins are discovered and registered; they do not bypass layer import contracts.
2. Sandbox and lifecycle hooks are mandatory for untrusted or swappable engines.
3. Prefer stub plugins in tests.
4. New engine backends land as plugins/adapters in an explicit sprint — not ad-hoc scripts.

## Related Docs

- `docs/architecture/plugin_architecture.md`
- Phase 2: `ml_engine_plugins` README via package code
