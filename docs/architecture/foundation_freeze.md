# Foundation Architecture Freeze

**Version:** v1.0.0-foundation  
**Status:** Frozen — certified baseline before Execution layer

## Completed Layers

```
Services → Pipeline → Workflow → Plugins → Data → Core → ML → AI → Decision → Risk
```

Execution is **not** part of this freeze.

## Layer Responsibilities

| Layer | Responsibility |
|---|---|
| `services` | Application context, service registry, lifecycle |
| `pipeline` | Stage-based orchestration, pipeline registry |
| `workflow` | Job scheduling, checkpoints, recovery |
| `plugins` | Plugin discovery, loading, sandbox, lifecycle |
| `data` | Dataset registry, schema, lineage, persistence |
| `core` | CoreContext, entities, identifiers, runtime |
| `ml` | Models, training, inference, evaluation |
| `ai` | Agents, prompts, LLM contracts, reasoning, orchestration |
| `decision` | Decision engine, policies, evaluation |
| `risk` | Validation, scoring, approval contracts |

## Import Rules

Higher layers may import lower layers. Reverse imports are forbidden.

| Layer | Forbidden Imports |
|---|---|
| `services` | connectors |
| `pipeline` | connectors, ml, ai, risk, execution, api, dashboard |
| `workflow` | connectors, ml, ai, risk, execution, api, dashboard |
| `plugins` | connectors, ml, ai, llm, risk, execution, api, dashboard |
| `data` | connectors, core, ml, ai, decision, risk, execution, api, dashboard, research |
| `core` | connectors, ml, ai, decision, risk, execution, api, dashboard, research |
| `ml` | ai, decision, risk, execution, connectors, api, dashboard, research |
| `ai` | decision, risk, execution, connectors, api, dashboard, research |
| `decision` | risk, execution, connectors, api, dashboard, research |
| `risk` | execution, connectors, api, dashboard, research |

## Public API Freeze

All foundation layer packages export contracts exclusively via `__all__` in `__init__.py`:

- `services`, `pipeline`, `workflow`, `plugins`
- `data`, `core`, `ml`, `ai`, `decision`, `risk`

See `docs/architecture/foundation/api_inventory.md` for the complete inventory.

## Certification

```bash
python scripts/foundation_certification.py
```

Output:
- `FOUNDATION_CERTIFICATION.md` — master certification document
- `docs/architecture/foundation/` — archived reports

## Git Tag

```
v1.0.0-foundation
```

This tag marks the stable certified baseline for rollback and regression comparison.

## Change Control

Changes to frozen public APIs require an Architecture Change Proposal (ACP).

## Next Step

Task 11: Execution Foundation — authorized only after certification passes.
