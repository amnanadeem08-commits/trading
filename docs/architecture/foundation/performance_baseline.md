# Performance Baseline Report

**Generated:** 2026-07-10T02:41:51.081687+00:00

Median latency measurements (milliseconds). No optimisation applied.

| Component | Median (ms) |
|---|---|
| ai_orchestration_ms | 0.0947 |
| core_runtime_context_ms | 17.817 |
| data_registry_list_ms | 0.001 |
| decision_orchestration_ms | 0.0337 |
| ml_registry_list_ms | 0.0005 |
| pipeline_context_build_ms | 0.0018 |
| plugin_discover_ms | 0.0888 |
| risk_orchestration_ms | 0.0514 |
| workflow_registry_list_ms | 0.0008 |

## Notes

- Measurements use `time.perf_counter()` with 50 iterations (20 for orchestration).
- Results are environment-dependent baselines for regression comparison.
- Execution layer not included (not yet implemented).
