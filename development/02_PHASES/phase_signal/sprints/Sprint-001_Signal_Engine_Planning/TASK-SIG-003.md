# TASK-SIG-003 — Indicator and Rule Candidate Generator

## Sprint

Sprint-001 — Signal Engine Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Generate deterministic indicator_values and directional candidates for signal assembly.

## Objective

Generate deterministic indicator_values and directional candidates for signal assembly.

## Background

ExplainableSignal requires non-empty indicators_used and indicator_values. Legacy RSI/MACD logic must not remain only in dashboard.

## Scope

### Implementation Scope

Rule/indicator candidate module inside signal_engine (or allowed feature layer extension) producing structured candidates + indicator maps.

## Out of Scope

LLM calls; broker orders; full strategy marketplace.

## Dependencies

SIG-001, SIG-002

## Architecture Impact

Prefer pure functions / services; no hidden logic in API routes.

## Implementation Notes

Document which indicators are supported in TIOS trading reference cross-links.

## Files Expected

- candidate generator modules
- unit tests for RSI/MACD/etc. as scoped
- docs pointers under development/03_TRADING_REFERENCE if needed

## Tests Required

Unit tests with deterministic fixtures.

## Validation Gates

Full code gates + validate_tios

## Validation

Full code gates + validate_tios

## Acceptance Criteria

- [ ] Candidates include direction + indicator map
- [ ] Deterministic for fixed fixtures
- [ ] Wired to assembler inputs

## Status

done

## Completion Notes

Completed 2026-07-11. Indicators + RSIMACDRule + apply_candidate. Report: `SIG-003_COMPLETION_REPORT.md`. Next: SIG-004.

## Completion Report Format

When this task closes, write notes covering:

1. Files created / modified
2. Tests added and commands run
3. Architecture / import impact
4. Acceptance criteria checklist (all [x])
5. Remaining risks / debt
6. Recommended next task ID
7. Run `python scripts/sync_tios_status.py` and `python scripts/validate_tios.py`

