# Adapter Architecture

## Framework Adapters

Package: `framework_adapters`

- Contracts: capability, manifest, metadata, `FrameworkAdapter`
- Factory + resolver
- Runtime: `AdapterRuntime`, `ModelRuntimeManager`, session registry
- Implementations: stub + ORT (`onnx_framework_adapter` / executor path)
- Must **not** import `artifact_management` or `storage_providers` directly

## Connector Adapters

Package: `connectors`

- Exchange/paper/simulation adapters
- Base connector freeze from Phase 0
- Live broker automation remains disabled until V1.5 approval

## Bridge Pattern

Owning packages expose `integration/*_bridge.py` to wire neighbors without illegal reverse imports.

Examples:

- `inference_execution_bridge` in `framework_adapters`
- `model_registry_bridge` in `inference_pipeline`
- Storage → artifact bridges in storage/artifact packages
