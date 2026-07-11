# Task Template

Copy into the active sprint folder as `TASK-<ID>.md` (example: `TASK-SIG-001.md`).

Required sections (exact headings):

```markdown
# TASK-<ID> — Title

## Sprint

## Goal

## Scope

## Out of Scope

## Dependencies

## Architecture Impact

## Implementation Notes

## Files Expected

## Tests Required

## Validation Gates

## Acceptance Criteria

## Status

## Completion Notes
```

Status values: `todo` | `in_progress` | `blocked` | `done` | `cancelled`

Rules:

- One task file = one implementable unit.
- Register the task ID in `00_MASTER/TASK_INDEX.md` and `00_MASTER/NEXT_TASK.md` when it becomes active.
- Do not start work unless Status is `in_progress` and it is listed as current in `NEXT_TASK.md`.
