# TASK-PAPER-005 — Paper Lifecycle Events and Audit

## Sprint

Sprint-002 — Paper Trading Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Emit domain events and audit records for paper order lifecycle (created, filled, rejected, cancelled).

## Scope

### Implementation Scope

Lifecycle service hooks; EventBus publish; AuditLogger writes; align with trade lifecycle docs.

## Out of Scope

External notification providers; mobile push.

## Dependencies

PAPER-001 through PAPER-004

## Architecture Impact

Use `events` / `audit` governance packages; no dashboard coupling.

## Implementation Notes

Rejected paper attempts must be explicit with reasons in payload/audit.

## Files Expected

- lifecycle module
- tests for emit-on-fill and emit-on-reject

## Tests Required

Unit + integration

## Validation Gates

Full code gates + validate_tios

## Acceptance Criteria

- [ ] Events emitted on fill
- [ ] Audit written on fill/reject
- [ ] Lifecycle doc still accurate

## Status

todo

## Completion Notes

_Not started._
