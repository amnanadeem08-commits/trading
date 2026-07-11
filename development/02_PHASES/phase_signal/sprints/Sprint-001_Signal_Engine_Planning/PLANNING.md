# Signal Engine Planning Package — Sprint-001

**Task:** SIG-PLAN-001  
**Type:** Planning only  
**Result target:** Complete planning; hand off to SIG-001  
**Date:** 2026-07-11

## Sprint Goal

Define everything required to implement Signal Engine V1.0 under TIOS without writing production feature code in this sprint.

## Sprint Scope

Documentation, dependency mapping, architecture boundaries, milestones, task breakdown, gates, risks, debt, and exit criteria for explainable signal generation.

## Deliverables

| Deliverable | Path |
|-------------|------|
| Phase README | `../../README.md` |
| Sprint record | `SPRINT.md` |
| This planning package | `PLANNING.md` |
| Planning task | `TASK-SIG-PLAN-001.md` |
| Implementation tasks | `TASK-SIG-001.md` … `TASK-SIG-008.md` |
| Completion report | `COMPLETION_REPORT.md` |
| Status / next-task sync | `00_MASTER/*`, `10_STATUS/*` |

## Architecture Boundaries

```text
market_data / historical
        ↓
feature_engineering / feature_store
        ↓
(indicator / rule candidates)     inference_pipeline → ml_runtime → adapters
        ↓                                    ↓
        └──────────► signal_engine (planned) ◄── ai (LLM insight)
                              ↓
                         decision (policies)
                              ↓
                           risk (assessment)
                              ↓
                    ExplainableSignal (models.signal)
                              ↓
                    events / audit (emit + record)
```

### Allowed

- Build on existing `models.signal.ExplainableSignal`, `InvalidationRule`, `Provenance`
- Use bridges; respect `pyproject.toml` import-linter contracts
- Keep business logic in services/domain packages — not API/dashboard routes

### Forbidden

- Reverse imports
- Production import of `research`
- Enabling broker / live order paths
- Parallel “shadow” signal schemas that bypass explainability validators
- Weakening typing or coverage

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Phase 0 models | Certified | `ExplainableSignal` already exists |
| Foundation decision/risk/ai/ml | Certified | Consume; do not rewrite |
| Phase 2 ML stack | Complete | Inference path available |
| Legacy `main.py` / dashboard | Legacy | Do not grow; migrate concepts into platform tasks |
| TIOS | Complete | Governs delivery |

## Milestones

| Milestone | Meaning | Gate |
|-----------|---------|------|
| M0 | Planning complete (this sprint) | `validate_tios.py` PASS |
| M1 | Signal package skeleton + contracts wiring (SIG-001) | unit + architecture |
| M2 | Feature/indicator candidate path (SIG-002–003) | unit + integration |
| M3 | ML + LLM attachment (SIG-004–005) | unit + integration |
| M4 | Risk/confidence/invalidation + validation/events (SIG-006–007) | unit + architecture |
| M5 | E2E signal suite + docs (SIG-008) | full gates ≥88% coverage |

## Task Breakdown

| ID | Title | Depends on | Status after planning |
|----|-------|------------|------------------------|
| SIG-PLAN-001 | Open planning sprint | — | done |
| SIG-001 | Signal engine package skeleton + assembly API | Planning | todo (next) |
| SIG-002 | Market/feature intake adapters for signals | SIG-001 | todo |
| SIG-003 | Indicator/rule candidate generator | SIG-001, SIG-002 | todo |
| SIG-004 | ML prediction attachment via inference path | SIG-001 | todo |
| SIG-005 | LLM insight / explainability attachment | SIG-001, SIG-004 | todo |
| SIG-006 | Confidence, risk assessment, invalidation binding | SIG-001 | todo |
| SIG-007 | Signal validation, registry, lifecycle events | SIG-001–006 | todo |
| SIG-008 | E2E tests, lifecycle docs sync, V1.0 readiness checklist | SIG-007 | todo |

## Acceptance Criteria (Planning Sprint)

- [x] All planning sections present
- [x] SIG-001…SIG-008 task files follow TIOS task template
- [x] Architecture boundaries explicit
- [x] No production feature code
- [x] TIOS sync + validate pass
- [x] NEXT_TASK points to SIG-001 as next implementation task

## Validation Gates

Planning sprint gates:

1. `python scripts/sync_tios_status.py`
2. `python scripts/validate_tios.py`

Future implementation gates (for SIG-001+): full set in `development/05_VALIDATION/GATES.md` including architecture, import-linter, pytest, coverage ≥88%.

## Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R1 | Rebuilding legacy dashboard logic inside platform | Explicit out-of-scope; migrate via tasks only |
| R2 | Import-linter violations when wiring ML/AI | Plan bridges; review contracts before coding |
| R3 | Incomplete explainability | Mandatory `ExplainableSignal` validator fields |
| R4 | Scope creep into paper/broker | Hard out-of-scope until V1.2 / V1.5 |
| R5 | Dual NEXT_TASK paths drift | `sync_tios_status.py` mirrors `10_STATUS/NEXT_TASK.md` |

## Technical Debt (Planning Notes)

| ID | Note | Carry into |
|----|------|------------|
| TD-SIG-01 | Legacy CLI/dashboard still parallel UX | SIG-008 docs; later deprecation sprint |
| TD-SIG-02 | No dedicated `signal_engine` package yet | SIG-001 |
| TD-SIG-03 | Sentiment / confidence product engines still roadmap | Not V1.0 core; optional later |

## Exit Criteria

Planning sprint may close only when:

1. This document and all task files exist and validate
2. `COMPLETION_REPORT.md` written
3. `NEXT_TASK` active task = **SIG-001** (ready, not implemented)
4. `validate_tios.py` exits 0
5. No production Signal Engine code was added
