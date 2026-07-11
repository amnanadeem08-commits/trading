# TASK-SIG-007 — Signal Validation, Registry, and Lifecycle Events

## Sprint

Sprint-001 — Signal Engine Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Add signal validation service, in-memory/registry record, and event/audit emission for signal lifecycle.

## Objective

Add signal validation service, in-memory/registry record, and event/audit emission for signal lifecycle.

## Background

TIOS lifecycle docs require explicit states; models.events already has signal-related event shapes.

## Scope

### Implementation Scope

Validator, registry, emit SignalCreated (or equivalent) via events; align with `08_DOCUMENTATION/signal_lifecycle.md`.

## Out of Scope

External notification providers; mobile alerts product.

## Dependencies

SIG-001 through SIG-006 (assembly path usable)

## Architecture Impact

Use events/audit per contracts; no dashboard coupling.

## Implementation Notes

Rejected signals must be explicit with reasons.

## Files Expected

- validation + registry modules
- event emission hooks
- tests

## Tests Required

Unit + integration for accept/reject paths.

## Validation Gates

Full code gates + validate_tios

## Validation

Full code gates + validate_tios

## Acceptance Criteria

- [x] Accept/reject paths tested
- [x] Events emitted on create
- [x] Lifecycle doc still accurate

## Status

done

## Completion Notes

Completed 2026-07-11. Validator + lifecycle service + events/audit. Report: `SIG-007_COMPLETION_REPORT.md`. Next: SIG-008.

## Completion Report Format

When this task closes, write notes covering:

1. Files created / modified
2. Tests added and commands run
3. Architecture / import impact
4. Acceptance criteria checklist (all [x])
5. Remaining risks / debt
6. Recommended next task ID
7. Run `python scripts/sync_tios_status.py` and `python scripts/validate_tios.py`
