# TASK-PAPER-004 — Simulation Fill and Position/PnL Ledger

## Sprint

Sprint-002 — Paper Trading Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Execute deterministic simulated fills via existing simulation/paper scaffolds and record position + PnL ledger entries.

## Scope

### Implementation Scope

Wire paper adapter/simulation engine; append-only ledger models for positions and simulated PnL.

## Out of Scope

Live settlement; real money transfers; broker reconciliation product.

## Dependencies

PAPER-001 through PAPER-003

## Architecture Impact

Reuse `connectors.adapters.paper` / `SimulationEngine`; add ledger types under paper_trading or models as appropriate (prefer additive).

## Implementation Notes

PnL is simulated for learning/review only — never framed as guaranteed returns.

## Files Expected

- fill orchestration
- ledger module
- unit/integration tests

## Tests Required

Unit + integration

## Validation Gates

Full code gates + validate_tios

## Acceptance Criteria

- [ ] Simulated fill recorded
- [ ] Position/PnL ledger updated
- [ ] Deterministic replay-friendly behavior

## Status

todo

## Completion Notes

_Not started._
