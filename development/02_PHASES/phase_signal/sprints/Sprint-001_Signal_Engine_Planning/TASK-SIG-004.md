# TASK-SIG-004 — ML Prediction Attachment via Inference Path

## Sprint

Sprint-001 — Signal Engine Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Attach `MLPrediction` to signals using Phase 2 inference/runtime path without illegal imports.

## Objective

Attach `MLPrediction` to signals using Phase 2 inference/runtime path without illegal imports.

## Background

Phase 2 provides inference_pipeline and ml_runtime. Signal Engine should consume predictions through allowed bridges.

## Scope

### Implementation Scope

Integration module mapping inference outputs → MLPrediction on ExplainableSignal; tests with stub/ORT-safe fixtures.

## Out of Scope

New model training; new framework adapters; live broker.

## Dependencies

SIG-001; inference_pipeline / ml_runtime available via legal wiring.

## Architecture Impact

Do not import forbidden modules from signal_engine. Prefer dependency inversion / bridges owned correctly.

## Implementation Notes

decision_source ML_ONLY / AI_ENHANCED_ML requirements must remain enforceable.

## Files Expected

- ml attachment bridge/adapter
- tests with stub inference

## Tests Required

Unit + integration (stub engine).

## Validation Gates

Full code gates + validate_tios

## Validation

Full code gates + validate_tios

## Acceptance Criteria

- [ ] MLPrediction attached when required
- [ ] Failure modes explicit (no silent drop)
- [ ] Import-linter green

## Status

done

## Completion Notes

Completed 2026-07-11. ML attach mapper/port/stub. Report: `SIG-004_COMPLETION_REPORT.md`. Next: SIG-005.

## Completion Report Format

When this task closes, write notes covering:

1. Files created / modified
2. Tests added and commands run
3. Architecture / import impact
4. Acceptance criteria checklist (all [x])
5. Remaining risks / debt
6. Recommended next task ID
7. Run `python scripts/sync_tios_status.py` and `python scripts/validate_tios.py`

