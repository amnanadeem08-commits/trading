# Next Task

**Last synced:** 2026-07-12
**Authority:** Must stay in sync with `PROJECT_STATUS.md`, `CHANGELOG.md`, and `TASK_INDEX.md`.  
**Mirror:** `development/10_STATUS/NEXT_TASK.md`.

## Current

| Field | Value |
|-------|--------|
| Active coding task | **PAPER-004** |
| Current task | PAPER-004 |
| Status | READY |
| Title | Simulation Fill and Position/PnL Ledger |
| Task document | `development/02_PHASES/phase_paper/sprints/Sprint-002_Paper_Trading_Planning/TASK-PAPER-004.md` |
| Phase | `phase_paper` |
| Allowed work | Implement PAPER-004 only |
| Forbidden | PAPER-005+; live broker automation |

## Recently Completed

| ID | Title | Result |
|----|-------|--------|
| PAPER-003 | Risk Gate Before Simulated Fill | Complete |
| PAPER-002 | Signal to Paper Order Request Mapping | Complete |
| PAPER-001 | Paper Trading Package Skeleton and Orchestration API | Complete |
| PAPER-PLAN-001 | Open Paper Trading Planning Sprint | Complete |

## Queue

| Priority | ID | Title |
|----------|----|-------|
| 1 | PAPER-004 | Simulation fill + ledger |
| 2 | PAPER-005 | Lifecycle events + audit |
| 3 | PAPER-006 | Journal / review contracts |
| 4 | PAPER-007 | E2E + V1.2 readiness |

## Sync Commands

```bash
python scripts/sync_tios_status.py
python scripts/validate_tios.py
```

**Note:** Signal Engine V1.0 path remains accepted; this queue is Paper Trading V1.2.
