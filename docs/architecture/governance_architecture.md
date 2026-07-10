# Governance Architecture

## Purpose

Governance layers enforce traceability, reproducibility, safe rollout, and research isolation across the platform.

## Components

| Package | Responsibility |
|---|---|
| `events/` | In-process event bus, append-only persistence interface, replay scaffold |
| `versioning/` | In-memory version registries for models, prompts, strategies, connectors, schemas |
| `audit/` | Append-only audit write/read/export/replay contracts |
| `feature_flags/` | Runtime feature flag resolution: defaults → YAML → environment |
| `research/` | Promotion gate interface only — no production logic |

## Event Bus (Rule R13)

- `EventBus.publish()` persists then dispatches to subscribers
- `subscribe()` / `unsubscribe()` for typed handlers
- `EventPersistenceStore` is append-only
- `EventReplayer` replays without republishing
- In-process only in Phase 0 — no Redis/Kafka/RabbitMQ

## Versioning (Rule R14)

Each registry supports:

- `register(version)`
- `get(version_id)`
- `current()`
- `list_versions()`
- `exists(version_id)`

No database in Phase 0.

## Audit (Rule R15)

- `AuditLogger.write()`
- `AuditReader.read()`
- `AuditExporter.export_json()`
- `AuditReplayer.replay()`
- Append-only `AuditStore` contract — no external persistence in Phase 0

## Feature Flags (Rule R16, R17)

Resolution order (later overrides earlier):

1. `FeatureFlagDefaults` — production-safe defaults
2. `YamlFeatureFlagProvider` — `config/feature_flags.yaml`
3. `EnvironmentFeatureFlagProvider` — `FEATURE_FLAG_<NAME>`

## Research Isolation (Rule R9)

- `PromotionGate` is abstract
- Production packages must not import `research/`
- No experiments, RL, or optimization in Phase 0

## Dependency Rules

```
models  ←  events, versioning, audit, feature_flags, research
config  ←  feature_flags
```

Governance packages must not import: `connectors`, `services`, `ml`, `ai`, `research` (except within research itself).
