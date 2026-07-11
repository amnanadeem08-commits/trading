# TASK-PAPER-001 — Paper Trading Package Skeleton and Orchestration API

## Sprint

Sprint-002 — Paper Trading Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Create `paper_trading/` (or equivalent) package skeleton with typed orchestration API that coordinates signal → paper path without live brokers.

## Scope

### Implementation Scope

Package layout, public contracts, registry stub, config YAML stub, unit tests, import-linter wiring if required.

## Out of Scope

Fill simulation productization; broker adapters; UI.

## Dependencies

PAPER-PLAN-001; Signal Engine V1.0; existing paper adapter scaffolds.

## Architecture Impact

New package must respect import-linter; may use models/events/audit/risk/signal_engine/connectors.paper as allowed; must not enable live trading.

## Implementation Notes

Prefer orchestration over rewriting `PaperExecutionAdapter`. Confidence/PnL are simulated — not profit guarantees.

## Files Expected

- `paper_trading/` skeleton
- config stub
- unit tests

## Tests Required

Unit tests for package imports and orchestration stubs.

## Validation Gates

Full code gates + validate_tios

## Acceptance Criteria

- [x] Package importable
- [x] Orchestration API stub present
- [x] Import-linter green
- [x] Live trading remains disabled

## Status

done

## Completion Notes

Completed 2026-07-11. Package + orchestrator + registry. Report: `PAPER-001_COMPLETION_REPORT.md`. Next: PAPER-002.
