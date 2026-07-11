# Phase 2 — ML Execution Platform

**Status:** Complete (infrastructure)  
**Focus:** Real inference path without new architecture layers beyond established packages

## Packages

| Package | Role |
|---------|------|
| `market_data` | Streams, normalization, market models |
| `historical` | Datasets, query, replay |
| `feature_engineering` | Extraction, schema, feature models |
| `feature_store` | Catalog, cache, repository |
| `training_pipeline` | Jobs, experiments, checkpoints |
| `model_registry` | Catalog, lineage, promotion |
| `inference_pipeline` | Binding, schema, execution pipeline |
| `ml_runtime` | Sessions, executor registry |
| `ml_engine_plugins` | Engine plugin discovery/lifecycle |
| `framework_adapters` | ORT/stub adapters, model session manager |
| `artifact_management` | Manifests, cache, resolver |
| `storage_providers` | Local provider, path sandbox |

## Integration Pattern

Bridges live in the owning package. Lower packages must not import forbidden higher layers (see import-linter).

Example flow: storage resolve → artifact → adapter load/session → inference execution → ML runtime execute.

## Non-goals (still roadmap)

Sentiment productization, confidence engine product surface, live broker automation.
