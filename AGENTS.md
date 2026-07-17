# Agents — Start Here

This repository is controlled by **TIOS** (Trading Intelligence Operating System).

## Required reading before any coding task

1. [`development/00_MASTER/MASTER_ROADMAP.md`](development/00_MASTER/MASTER_ROADMAP.md)
2. [`development/00_MASTER/PROJECT_STATUS.md`](development/00_MASTER/PROJECT_STATUS.md)
3. [`development/00_MASTER/NEXT_TASK.md`](development/00_MASTER/NEXT_TASK.md) (mirror: [`development/10_STATUS/NEXT_TASK.md`](development/10_STATUS/NEXT_TASK.md))
4. Current sprint under [`development/02_PHASES/`](development/02_PHASES/)
5. Active `TASK-*.md` referenced by NEXT_TASK
6. [`development/01_GLOBAL_RULES/RULEBOOK.md`](development/01_GLOBAL_RULES/RULEBOOK.md)
7. [`development/01_GLOBAL_RULES/ARCHITECTURE_RULES.md`](development/01_GLOBAL_RULES/ARCHITECTURE_RULES.md)
8. [`development/07_CURSOR/WORKFLOW.md`](development/07_CURSOR/WORKFLOW.md)

Do not implement features outside `NEXT_TASK.md`. Do not skip validation gates.  
Before stopping: `python scripts/sync_tios_status.py` then `python scripts/validate_tios.py`.

## Cursor Cloud specific instructions

Python-only project. It **requires Python 3.14** (`pyproject.toml`), while the base image ships 3.12. A Python 3.14 virtualenv is pre-provisioned at `/workspace/.venv` (created with `uv`; `uv` lives at `~/.local/bin/uv`). The update script refreshes deps into that venv, so just activate it:

```bash
source /workspace/.venv/bin/activate
```

Run everything with that venv active. Standard commands are in `README.md` / `scripts/dev.py` / `GATES.md`:
- Lint: `python scripts/dev.py lint` · Format check: `python -m black --check <pkgs>`
- Tests: `python scripts/dev.py test` · Architecture: `python scripts/validate_architecture.py`
- TIOS gates: `python scripts/validate_tios.py`, `python scripts/sync_tios_status.py`

Non-obvious caveats (as of this setup):
- **Pre-existing failures unrelated to the environment**: `python scripts/dev.py test` shows ~15 failures (`tests/architecture/test_forbidden_imports.py` and `tests/unit/test_config_hash.py`) because the last commit added the `signal_engine`/`paper_trading` layers and `config/paper_trading.yaml` but their hardcoded expectation sets/counts were not updated. `dev.py lint` and `black --check` also report drift because CI installs **unpinned** `ruff`/`black` (now newer than the pre-commit-pinned 0.9.10 / 24.10.0). These are code/version drift, not setup problems.
- **`openai` dependency**: `core/llm_analyzer.py` (used by `main.py`/`dashboard.py`) imports `openai`, which was missing from `requirements.txt` — it has been added there.
- **Network**: PSX + PMEX market data (Yahoo Finance via `yfinance`) works. **Binance crypto is geo-blocked (HTTP 451)** in this environment, so live crypto scans fail; PSX/PMEX scans succeed.

### Running the app (Streamlit dashboard)
`streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true`

The dashboard only renders a workbook found under `outputs/production/` that (a) has `generator=production_scan` and (b) matches the configured universe; markets **absent** from the workbook are skipped in that check. Full "Refresh Results" needs an LLM key (`OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY`) **and** live crypto. To populate the dashboard **without any LLM key**, generate a technical-rules workbook from the reachable markets:

```bash
python scripts/seed_production_workbook_technical.py   # scans crypto+psx+pmex; crypto rows error out under geo-block
```

Because crypto is geo-blocked, seed only the reachable markets (PSX+PMEX) if you need a workbook the dashboard will accept (omit crypto so its universe check is skipped) — reuse `scripts/seed_production_workbook_technical.py`'s `_scan`/`_signal_from_technicals` with just PSX+PMEX and `main.save_results`.
