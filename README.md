# Khaldun Trade

AI-powered trading intelligence platform for **cryptocurrency**, **PMEX**, and **PSX**.

Current product objective: **signal generation and paper trading**.  
Broker automation stays **disabled** until explicitly approved.  
This is **not** financial advice and does **not** claim guaranteed profits.

## Start Here — TIOS

The **Trading Intelligence Operating System (TIOS)** is the single source of truth for architecture, roadmap, sprints, validation, and documentation.

1. [`development/00_MASTER/MASTER_ROADMAP.md`](development/00_MASTER/MASTER_ROADMAP.md)
2. [`development/00_MASTER/PROJECT_STATUS.md`](development/00_MASTER/PROJECT_STATUS.md)
3. [`development/07_CURSOR/WORKFLOW.md`](development/07_CURSOR/WORKFLOW.md)
4. [`AGENTS.md`](AGENTS.md)

Every coding task must begin by reading TIOS.

## Platform Baseline

| Milestone | Status |
|-----------|--------|
| Phase 0 contracts | Certified — `PHASE0_CERTIFICATION.md` |
| Foundation v1.0.0 | Certified — `FOUNDATION_CERTIFICATION.md` |
| Phase 2 ML execution | Complete in codebase |
| TIOS | Bootstrap complete (Sprint-000) |

Engineering archive: [`docs/`](docs/).

## Development Commands

```bash
python scripts/dev.py lint
python scripts/dev.py test
python scripts/validate_architecture.py
```

Coverage fail-under: **88%**. Full gates: [`development/05_VALIDATION/GATES.md`](development/05_VALIDATION/GATES.md).

## Legacy Signal Dashboard (Pre-Platform)

The original CLI/dashboard entrypoints remain for reference:

```bash
pip install -r requirements.txt
python main.py --market both
streamlit run dashboard.py
```

Configure LLM keys via `.env` (see `.env.example`). These paths are **legacy** relative to the platform packages and must not become the home of new business logic. Prefer TIOS-governed sprints for new work.
