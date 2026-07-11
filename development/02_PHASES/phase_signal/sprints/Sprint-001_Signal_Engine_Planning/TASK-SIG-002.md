# TASK-SIG-002 — Market and Feature Intake for Signals

## Sprint

Sprint-001 — Signal Engine Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Provide intake adapters that map market_data / feature_store snapshots into Signal Engine input DTOs.

## Objective

Provide intake adapters that map market_data / feature_store snapshots into Signal Engine input DTOs.

## Background

Signals need reproducible feature snapshots and market identifiers for Provenance.

## Scope

### Implementation Scope

Intake mappers/bridges from allowed neighbors into signal_engine input models; unit tests; no dashboard code.

## Out of Scope

New exchanges; live streaming product UI; training pipeline changes.

## Dependencies

SIG-001; market_data; feature_engineering/feature_store contracts.

## Architecture Impact

Use bridges; signal_engine must not violate forbidden imports toward higher layers.

## Implementation Notes

Preserve feature_snapshot_version and market_id in provenance fields.

## Files Expected

- `signal_engine/intake/` or integration bridges
- tests for mapping/validation

## Tests Required

Unit + focused integration with feature/market fixtures.

## Validation Gates

Full code gates in GATES.md + validate_tios

## Validation

Full code gates in GATES.md + validate_tios

## Acceptance Criteria

- [ ] Intake DTOs documented and tested
- [ ] Provenance fields populated from intake
- [ ] Import contracts green

## Status

done

## Completion Notes

Completed 2026-07-11. Intake DTOs/mappers + provenance builder landed. Report: `SIG-002_COMPLETION_REPORT.md`. Next: SIG-003.

## Completion Report Format

When this task closes, write notes covering:

1. Files created / modified
2. Tests added and commands run
3. Architecture / import impact
4. Acceptance criteria checklist (all [x])
5. Remaining risks / debt
6. Recommended next task ID
7. Run `python scripts/sync_tios_status.py` and `python scripts/validate_tios.py`

