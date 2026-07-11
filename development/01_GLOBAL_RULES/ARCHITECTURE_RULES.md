# Architecture Rules

## Source of Truth

- Import contracts: `pyproject.toml` → `[tool.importlinter]`
- Runtime/AST enforcement: `architecture/` + `scripts/validate_architecture.py`
- Frozen foundation: `docs/architecture/foundation_freeze.md`
- Layer diagrams: `../09_DIAGRAMS/`

## Dependency Direction

1. Phase 0 scaffolds and shared contracts sit at the base (`models`, `config`, `events`, …).
2. Foundation intelligence layers follow:  
   `services → pipeline → workflow → plugins → data → core → ml → ai → decision → risk`
3. Phase 2 ML stack (simplified allowed flow):  
   `market_data → historical → feature_engineering → feature_store → training_pipeline → model_registry → inference_pipeline → ml_runtime → ml_engine_plugins → framework_adapters → artifact_management → storage_providers`  
   (bridges live in the owning package; reverse package imports are forbidden).
4. `execution` must not import `connectors` (and related forbidden modules per import-linter).
5. Production must not import `research`.

## Allowed Imports

- A package may import packages that are **not** listed in its forbidden contract.
- Shared typed contracts should come from `models/` and package public `__all__` exports.
- Integration bridges may wire to the **next** allowed neighbor without importing forbidden upstream layers into a lower package.

## Forbidden Imports

Enforce via import-linter. Notable examples:

| Package | Must not import (examples) |
|---------|----------------------------|
| `framework_adapters` | `artifact_management`, `storage_providers`, `ml`, `ai`, `decision`, `risk`, `execution`, `connectors`, … |
| `inference_pipeline` | `ml_runtime`, `framework_adapters`, `artifact_management`, `storage_providers`, … |
| `ml` | `ai`, `decision`, `risk`, `execution`, `connectors`, … |
| Foundation packages | `connectors`, `research` (as contracted) |

Full list: `pyproject.toml`.

## Plugin Architecture

- Discovery, registry, lifecycle, sandbox patterns live in `plugins/` and specialized plugin packs (e.g. `ml_engine_plugins/`).
- Engines are swappable; stub engines are valid for tests.

## Adapter Architecture

- Framework engines integrate through `framework_adapters` contracts + factory + runtime manager.
- Brokers/exchanges integrate through `connectors` adapters.
- Adapters must not pull forbidden layers; resolve paths via bridges owned by higher layers.

## Repository Architecture

- Persistence and catalogs use registry/repository modules inside their package (`feature_store`, `model_registry`, `artifact_management`, etc.).
- No cross-cutting “god repository” that bypasses layer contracts.

## Change Control

Changes to frozen public APIs require an Architecture Change Proposal and explicit approval. Prefer additive contracts.
