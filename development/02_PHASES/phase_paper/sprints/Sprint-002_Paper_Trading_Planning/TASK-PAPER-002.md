# TASK-PAPER-002 — Signal to Paper Order Request Mapping

## Sprint

Sprint-002 — Paper Trading Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Map `ExplainableSignal` / assembly outputs into typed paper order requests for the paper adapter.

## Scope

### Implementation Scope

Mapper from signal contracts to paper request DTOs; explicit reject when signal lacks required fields.

## Out of Scope

Live order routing; portfolio sizing product UI.

## Dependencies

PAPER-001

## Architecture Impact

`paper_trading` may import `signal_engine` / `models` as allowed by layers.

## Implementation Notes

Rejected mappings must include reasons. Do not invent prices without market context when required.

## Files Expected

- request mapper module
- unit tests for accept/reject mapping

## Tests Required

Unit tests

## Validation Gates

Full code gates + validate_tios

## Acceptance Criteria

- [x] Valid signals map to paper requests
- [x] Invalid signals reject with reasons
- [x] No live broker types introduced

## Status

done

## Completion Notes

Completed 2026-07-11. Mapper + adapter bridge. Report: `PAPER-002_COMPLETION_REPORT.md`. Next: PAPER-003.
