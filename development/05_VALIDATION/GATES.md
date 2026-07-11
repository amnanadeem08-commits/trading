# Validation Gates

No sprint is complete until all applicable gates pass.

## Local / Script Gates

| Gate | Command / check |
|------|-----------------|
| Compile | `python -m compileall` on production packages |
| Lint | `ruff check` / `python scripts/dev.py lint` |
| Format | `black --check` |
| Types | `mypy` (strict) |
| Tests | `pytest` / `python scripts/dev.py test` |
| Coverage | fail-under **88%** (`pyproject.toml` / coverage workflow) |
| Architecture | `python scripts/validate_architecture.py` |
| Import contracts | import-linter (CI `architecture.yml`) |
| Configuration | `python scripts/validate_configuration.py` |
| Dependencies | `python scripts/validate_dependencies.py` |
| Environment | `python scripts/validate_environment.py` (when relevant) |
| Release readiness | `python scripts/validate_release.py` / `python scripts/release.py` |
| **TIOS integrity** | `python scripts/validate_tios.py` |
| **TIOS status sync** | `python scripts/sync_tios_status.py` (then re-validate) |
| Security posture | Review `security/` contracts; no secrets in git; broker flags off |
| Performance | Respect baselines in `docs/architecture/foundation/performance_baseline.md` when touching hot paths |
| Documentation | Update status / changelog / debt / next task / sprint report; no false done claims |

## CI Workflows (must match)

| Workflow file | What it runs |
|---------------|--------------|
| `.github/workflows/lint.yml` | `ruff check`, `black --check` |
| `.github/workflows/typing.yml` | `mypy` |
| `.github/workflows/architecture.yml` | `validate_architecture.py`, import-linter, `tests/architecture` |
| `.github/workflows/tests.yml` | `pytest` package suites |
| `.github/workflows/coverage.yml` | `pytest` with `--cov-fail-under=88` |
| `.github/workflows/dependencies.yml` | `validate_dependencies.py` |
| `.github/workflows/release.yml` | `release.py` |

## Docs-Only / TIOS Sprints

For documentation-only work: still run `validate_tios.py` and `sync_tios_status.py`. Do not claim product features complete.
