# Cursor / Agent Workflow

Every future task in this repository must follow this workflow.

## Mandatory Read Order

1. `development/00_MASTER/MASTER_ROADMAP.md`
2. `development/00_MASTER/PROJECT_STATUS.md`
3. `development/00_MASTER/NEXT_TASK.md` (also mirrored at `development/10_STATUS/NEXT_TASK.md`)
4. The **current sprint** folder under `development/02_PHASES/`
5. The **active TASK-*.md** referenced by NEXT_TASK
6. `development/01_GLOBAL_RULES/RULEBOOK.md`
7. `development/01_GLOBAL_RULES/ARCHITECTURE_RULES.md`
8. Relevant validation, architecture, trading, or AI docs for the task

If `NEXT_TASK.md` says Active coding task = **none**, do not invent product work.

## Execute

1. Implement **only** the task listed in `NEXT_TASK.md`
2. Task files must follow `02_PHASES/TASK_TEMPLATE.md`
3. Sprint files must follow `02_PHASES/SPRINT_TEMPLATE.md`
4. Do not expand scope from chat alone
5. Do not implement roadmap placeholders

## Validate

1. Run every gate in `development/05_VALIDATION/GATES.md`
2. Always run `python scripts/validate_tios.py`
3. Always run `python scripts/sync_tios_status.py` after status/task changes
4. Re-run `python scripts/validate_tios.py`

## Document

1. Update sprint/task files (files created/modified, tests, validation, acceptance)
2. Update `NEXT_TASK.md` (current + queue)
3. Update `PROJECT_STATUS.md`
4. Update `CHANGELOG.md` when milestone-worthy
5. Update `TECHNICAL_DEBT.md` if debt changed
6. Produce the standard completion report for the sprint/task
7. Run sync + validate scripts
8. **Stop**

## Cursor Rule

Project rule `.cursor/rules/tios-workflow.mdc` always applies and points here.

## Root Pointer

`AGENTS.md` at the repository root redirects agents to TIOS.
