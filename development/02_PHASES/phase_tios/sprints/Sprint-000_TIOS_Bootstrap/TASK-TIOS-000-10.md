# TASK-TIOS-000-10 — TIOS Integrity Verification

## Sprint

Sprint-000 — TIOS Bootstrap

## Goal

Verify TIOS is complete and reliable: links, phase READMEs, templates, Cursor workflow E2E, status sync, changelog/next-task sync, CI-matched gates, no broken/outdated refs.

## Scope

- Add `NEXT_TASK.md`, templates, E2E workflow test
- Add `scripts/validate_tios.py` and `scripts/sync_tios_status.py`
- Align `GATES.md` to CI workflow filenames
- Sync master docs and re-run validator to PASS

## Out of Scope

- Product Signal Engine implementation
- Broker automation
- Changes to frozen certification documents

## Dependencies

- Sprint-000 TIOS tree already created

## Architecture Impact

None to production packages. Process/docs/scripts only.

## Implementation Notes

Machine gate is `validate_tios.py`. Status snapshots refresh via `sync_tios_status.py`.

## Files Expected

- `development/00_MASTER/NEXT_TASK.md`
- `development/02_PHASES/*_TEMPLATE.md`
- `development/07_CURSOR/E2E_WORKFLOW_TEST.md`
- `scripts/validate_tios.py`
- `scripts/sync_tios_status.py`

## Tests Required

- Run `python scripts/validate_tios.py` (exit 0)

## Validation Gates

- TIOS integrity gate
- Documentation consistency

## Acceptance Criteria

- [x] All checklist items pass under `validate_tios.py`
- [x] `NEXT_TASK` / `CHANGELOG` / `PROJECT_STATUS` agree
- [x] CI workflow files referenced exactly in `GATES.md`

## Status

done

## Completion Notes

Validator PASSED (0 errors). Active coding task remains `none`.
