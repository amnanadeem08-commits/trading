# Repository Architecture

Registries and repositories are **package-local**. There is no cross-cutting god repository.

| Concern | Typical modules |
|---------|-----------------|
| Features | `feature_store` registry/repository/cache |
| Models | `model_registry` catalog/lineage/promotion |
| Artifacts | `artifact_management` registry/resolver/cache |
| Training | `training_pipeline` experiment/checkpoint registries |
| Inference | `inference_pipeline` inference registry |
| Adapters | `framework_adapters` adapter + model session registries |
| Datasets | `historical`, `data` registries |

## Rules

1. Persist via the owning package’s repository/registry API.
2. Do not reach into another package’s private storage modules.
3. Versioning and validation stay with the owning package.
