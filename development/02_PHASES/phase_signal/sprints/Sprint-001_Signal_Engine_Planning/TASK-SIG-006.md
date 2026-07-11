# TASK-SIG-006 — Confidence, Risk Assessment, and Invalidation Binding

## Sprint

Sprint-001 — Signal Engine Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Bind confidence scoring, `RiskAssessment`, and `InvalidationRule` into every assembled signal.

## Objective

Bind confidence scoring, `RiskAssessment`, and `InvalidationRule` into every assembled signal.

## Background

Directional decisions require confidence > 0; risk_assessment and invalidation are mandatory on ExplainableSignal.

## Scope

### Implementation Scope

Adapters to `risk` package scoring/assessment contracts; invalidation rule builder from structure/ATR/support inputs as available.

## Out of Scope

Portfolio sizing product; live order rejection UI.

## Dependencies

SIG-001; risk foundation package

## Architecture Impact

Respect decision→risk layering; signal_engine must not reverse-import illegally.

## Implementation Notes

Confidence is not probability of profit — document in API/docs.

## Files Expected

- risk/confidence binders
- invalidation builder
- unit tests

## Tests Required

Unit tests for BUY/SELL confidence rules and missing risk failures.

## Validation Gates

Full code gates + validate_tios

## Validation

Full code gates + validate_tios

## Acceptance Criteria

- [x] risk_assessment always set
- [x] invalidation always set
- [x] confidence rules enforced

## Status

done

## Completion Notes

Completed 2026-07-11. Risk/confidence/invalidation binders + ATR helper. Report: `SIG-006_COMPLETION_REPORT.md`. Next: SIG-007.

## Completion Report Format

When this task closes, write notes covering:

1. Files created / modified
2. Tests added and commands run
3. Architecture / import impact
4. Acceptance criteria checklist (all [x])
5. Remaining risks / debt
6. Recommended next task ID
7. Run `python scripts/sync_tios_status.py` and `python scripts/validate_tios.py`
