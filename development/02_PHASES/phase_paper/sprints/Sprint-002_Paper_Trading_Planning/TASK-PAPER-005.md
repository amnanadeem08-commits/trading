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

- [x] Events emitted on fill
- [x] Audit written on fill/reject
- [x] Lifecycle doc still accurate

## Status

**Complete** (2026-07-16)

## Completion Notes

- `paper_trading` lifecycle emits deterministic domain events and deterministic, append-only audit records for fill accepted + risk/rejection failures.
- Lifecycle events include stable IDs, timestamps, symbol, timeframe (`legacy_config.TIMEFRAME`), session id, signal id, and fill id where available.
- Idempotency is enforced by skipping event publication/audit write when an audit record for the same deterministic `event_id` already exists.
- Rejected fills emit explicit `fill_rejected` and `lifecycle_failure` outcomes with reasons, and do not mutate paper ledgers/portfolio.
