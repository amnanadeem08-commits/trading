# TASK-PAPER-006 — Journal and Review Contracts

## Sprint

Sprint-002 — Paper Trading Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Add typed journal/review contracts for post-trade paper review (notes, tags, lesson fields) without shipping a mobile/UI product.

## Scope

### Implementation Scope

Journal entry models + registry/store stub; link to paper execution/signal ids.

## Out of Scope

Full journaling UX product; social sharing; broker statements.

## Dependencies

PAPER-005

## Architecture Impact

Additive contracts; keep storage in-memory/stub unless existing store patterns apply.

## Implementation Notes

Journal text must not claim financial advice. Safety language in docs.

## Files Expected

- journal contracts + store stub
- unit tests

## Tests Required

Unit tests

## Validation Gates

Full code gates + validate_tios

## Acceptance Criteria

- [ ] Journal entry attachable to paper trade
- [ ] Retrieval by trade/signal id
- [ ] Safety notes in docs

## Status

todo

## Completion Notes

_Not started._
