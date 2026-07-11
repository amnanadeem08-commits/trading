# Dependencies — Allowed and Forbidden Imports

**Machine-enforced source of truth:** `pyproject.toml` `[tool.importlinter]` contracts.  
**Runtime/AST:** `scripts/validate_architecture.py`.

## Principles

1. No reverse imports across layer contracts.
2. Production must not import `research`.
3. Foundation packages must not import `connectors`.
4. Phase 2 packages must not import forbidden upstream ML/product layers listed in their contracts.
5. Integration uses **bridges in the owning package**, not illegal imports.

## Notable Forbidden Sets (Summary)

| Source | Forbidden examples |
|--------|--------------------|
| `pipeline` / `workflow` | `connectors`, `ml`, `ai`, `risk`, `execution`, `api`, `dashboard` |
| `historical` / `market_data` / `feature_engineering` | `connectors`, `core`, `ml`, `ai`, `decision`, `risk`, `execution`, services/pipeline/workflow, `research` |
| `feature_store` | `training_pipeline` and all later ML stack packages listed in contract |
| `training_pipeline` | `model_registry` and later stack |
| `model_registry` | `inference_pipeline` and later stack |
| `inference_pipeline` | `ml_runtime`, `framework_adapters`, `artifact_management`, `storage_providers`, … |
| `ml_runtime` | `ml_engine_plugins`, `framework_adapters`, … |
| `framework_adapters` | `artifact_management`, `storage_providers`, … |
| `artifact_management` | `storage_providers`, … |
| `execution` | `connectors`, `api`, `dashboard`, `research` |
| `ml` | `ai`, `decision`, `risk`, `execution`, `connectors`, … |
| `ai` | `decision`, `risk`, `execution`, `connectors`, … |
| `decision` | `risk`, `execution`, `connectors`, … |
| `risk` | `execution`, `connectors`, … |

## Allowed Integration Pattern (Conceptual)

Higher orchestration may call lower packages. Lower packages expose contracts; bridges wire neighbors without violating forbidden lists.

Always re-read the full contract list before adding imports.
