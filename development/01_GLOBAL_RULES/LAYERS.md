# Layer Responsibilities

## Phase 0

| Package | Responsibility |
|---------|----------------|
| `models` | Shared Pydantic contracts |
| `config` | Settings + YAML |
| `events` | In-process event bus |
| `versioning` | Version registries |
| `audit` | Append-only audit |
| `feature_flags` | Flag resolution |
| `research` | Promotion gate interface only |
| `architecture` | Enforcement engine |
| `health` / `metrics` / `platform_logging` / `security` / `notifications` / `monitoring` | Operational scaffolds |

## Foundation

| Package | Responsibility |
|---------|----------------|
| `services` | App context, service registry, lifecycle |
| `pipeline` | Stage orchestration |
| `workflow` | Jobs, checkpoints, recovery |
| `plugins` | Discovery, sandbox, lifecycle |
| `data` | Dataset registry, schema, lineage |
| `core` | CoreContext, entities, identifiers |
| `ml` | Training/inference/evaluation contracts |
| `ai` | Agents, prompts, LLM contracts, reasoning |
| `decision` | Decision engine, policies |
| `risk` | Validation, scoring, approval |

## Phase 2 ML

| Package | Responsibility |
|---------|----------------|
| `market_data` | Market stream and models |
| `historical` | Historical datasets and replay |
| `feature_engineering` | Feature extraction pipeline |
| `feature_store` | Feature datasets and cache |
| `training_pipeline` | Training jobs and experiments |
| `model_registry` | Model catalog and promotion |
| `inference_pipeline` | Input binding and inference execution pipeline |
| `ml_runtime` | Runtime sessions and executors |
| `ml_engine_plugins` | ML engine plugins |
| `framework_adapters` | Framework adapters + model session manager |
| `artifact_management` | Artifact registry and resolution |
| `storage_providers` | Storage backends |

## Execution / Connectors

| Package | Responsibility |
|---------|----------------|
| `execution` | Execution engine/orchestrator (no connector imports) |
| `signal_engine` | Assemble/register `ExplainableSignal` (V1.0 in progress) |
| `connectors` | Exchange/paper adapters |
