# Cursor Workflow — End-to-End Test

**Purpose:** Prove the mandatory agent read path exists and is consistent.  
**Last run:** 2026-07-11  
**Runner:** `python scripts/validate_tios.py` (workflow section)

## Steps

| # | Action | Expected path | Pass |
|---|--------|---------------|------|
| 1 | Open roadmap | `development/00_MASTER/MASTER_ROADMAP.md` | [x] |
| 2 | Open status | `development/00_MASTER/PROJECT_STATUS.md` | [x] |
| 3 | Open next task | `development/00_MASTER/NEXT_TASK.md` | [x] |
| 4 | Open current sprint | `development/02_PHASES/phase_tios/sprints/Sprint-000_TIOS_Bootstrap/SPRINT.md` | [x] |
| 5 | Open rulebook | `development/01_GLOBAL_RULES/RULEBOOK.md` | [x] |
| 6 | Open architecture rules | `development/01_GLOBAL_RULES/ARCHITECTURE_RULES.md` | [x] |
| 7 | Open gates | `development/05_VALIDATION/GATES.md` | [x] |
| 8 | Open Cursor workflow | `development/07_CURSOR/WORKFLOW.md` | [x] |
| 9 | Open always-apply rule | `.cursor/rules/tios-workflow.mdc` | [x] |
| 10 | Open root agent pointer | `AGENTS.md` | [x] |
| 11 | Confirm active task is none | `NEXT_TASK.md` says Active coding task = none | [x] |
| 12 | Sync status | `python scripts/sync_tios_status.py` | [x] |
| 13 | Validate TIOS | `python scripts/validate_tios.py` exits 0 | [x] |

## Result

**PASS** — workflow paths resolve; Sprint-000 complete; no active coding task; validator is the machine gate for this checklist.

## Failure Rule

If any step fails, do not start product coding. Fix TIOS first.
