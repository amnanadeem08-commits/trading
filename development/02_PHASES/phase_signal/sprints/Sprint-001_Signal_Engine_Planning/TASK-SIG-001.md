# TASK-SIG-001 — Signal Engine Package Skeleton and Assembly API

## Sprint

Sprint-001 — Signal Engine Planning (planning artifacts). Implementation work executes only when this ID is the Active coding task in NEXT_TASK.md.

## Goal

Create the Signal Engine service package skeleton and a typed assembly API that constructs `models.signal.ExplainableSignal` without bypassing explainability validators.

## Objective

Create the Signal Engine service package skeleton and a typed assembly API that constructs `models.signal.ExplainableSignal` without bypassing explainability validators.

## Background

ExplainableSignal already exists in Phase 0. V1.0 needs a platform-owned assembly/orchestration layer (not legacy dashboard).

## Scope

### Implementation Scope

New package (planned name `signal_engine/`) with public contracts, registry stubs, assembler interface, unit tests, config YAML stub, import-linter contract entry if required.

## Out of Scope

Indicator math, ML/LLM calls, risk scoring internals, connectors, paper trading.

## Dependencies

SIG-PLAN-001 complete; `models.signal`; foundation packages available for typed deps only as allowed.

## Architecture Impact

Must respect import-linter. Likely may use models/config/events; must not illegally import connectors/research. Add ACP only if frozen API change required (prefer additive).

## Implementation Notes

Objective: assembler accepts structured inputs and returns ExplainableSignal or validation errors. No TODO placeholders.

## Files Expected

- `signal_engine/` package modules
- `config/signal_engine.yaml`
- `tests/signal_engine/`
- possibly `pyproject.toml` import-linter addition

## Tests Required

Unit tests for assembler validation paths; architecture tests if new contracts added.

## Validation Gates

compileall, ruff, black, mypy, pytest, coverage≥88, validate_architecture, import-linter, validate_tios

## Validation

compileall, ruff, black, mypy, pytest, coverage≥88, validate_architecture, import-linter, validate_tios

## Acceptance Criteria

- [ ] Package importable with typed public API
- [ ] Assembler enforces ExplainableSignal invariants
- [ ] No reverse imports
- [ ] Coverage gate holds
- [ ] TIOS docs updated

## Status

done

## Completion Notes

Completed 2026-07-11. Package `signal_engine` ships assembler + registry + config. Report: `SIG-001_COMPLETION_REPORT.md`. Next task opened: SIG-002.

## Completion Report Format

When this task closes, write notes covering:

1. Files created / modified
2. Tests added and commands run
3. Architecture / import impact
4. Acceptance criteria checklist (all [x])
5. Remaining risks / debt
6. Recommended next task ID
7. Run `python scripts/sync_tios_status.py` and `python scripts/validate_tios.py`

