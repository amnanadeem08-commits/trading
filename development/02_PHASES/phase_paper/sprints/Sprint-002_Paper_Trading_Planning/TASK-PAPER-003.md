# TASK-PAPER-003 — Risk Gate Before Simulated Fill

## Sprint

Sprint-002 — Paper Trading Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Require an explicit risk check/gate before any simulated paper fill.

## Scope

### Implementation Scope

Bind risk assessment/verdict contracts into paper orchestration; fail closed on reject.

## Out of Scope

Live margin brokerage; portfolio optimizer product.

## Dependencies

PAPER-001, PAPER-002; foundation `risk` package

## Architecture Impact

Respect risk layering; no silent bypass of rejected verdicts.

## Implementation Notes

Paper fills after risk reject are forbidden. Document that risk gate ≠ profit protection guarantee.

## Files Expected

- risk gate binder
- unit + integration tests for reject path

## Tests Required

Unit + integration

## Validation Gates

Full code gates + validate_tios

## Acceptance Criteria

- [x] Risk reject blocks fill
- [x] Risk approve allows continuation
- [x] Reasons recorded on reject

## Status

done

## Completion Notes

Completed 2026-07-11. Risk gate binder + orchestrator authorization. Report: `PAPER-003_COMPLETION_REPORT.md`. Next: PAPER-004 (READY only — not started).
