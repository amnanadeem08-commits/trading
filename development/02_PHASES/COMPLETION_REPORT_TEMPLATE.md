# Completion Report Template

Copy to the sprint folder as `COMPLETION_REPORT.md` when closing a sprint (or a major task).

Required sections (exact headings):

```markdown
# Sprint-NNN Completion Report

**Sprint:**
**Date:**
**Type:**
**Result:**

## Delivered

## Validation

## Acceptance

## Next
```

Result values: `Complete` | `Partial` | `Failed`

After writing the report:

1. Run `python scripts/validate_tios.py`
2. Run `python scripts/sync_tios_status.py`
3. Update `CHANGELOG.md` if milestone-worthy
4. Point `NEXT_TASK.md` at the next work item (or `none`)
