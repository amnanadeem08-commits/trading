# Architecture Enforcement

## Purpose

The architecture enforcement layer prevents violations of Enterprise Architecture Blueprint v2.0 as the codebase grows. It is **infrastructure only** — no business logic, trading logic, connectors, ML, or AI.

## Components

| Component | Responsibility |
|---|---|
| `architecture/dependency_rules.py` | Frozen layer order, forbidden imports, legacy exclusions |
| `architecture/validators.py` | AST-based validation engine |
| `architecture/reporting.py` | Human-readable violation reports |
| `scripts/validate_architecture.py` | CLI entry point for local and CI validation |
| `tests/architecture/` | Pytest architecture enforcement suite |
| `import-linter` | Declarative import contracts in `pyproject.toml` |

## Pipeline Layer Direction (Rule R11)

Higher layers may import lower layers. Reverse imports fail validation.

```
connectors → data → core → ml → ai → agents → decision → risk → execution
```

## Forbidden Rules

| Rule | Enforcement |
|---|---|
| `services` imports `connectors/*` directly | `forbidden_import` + import-linter |
| `services` contains `if market` / `if exchange` | AST market-branching scan |
| `core` imports `ai` | `forbidden_import` |
| `core` imports `connectors` | `forbidden_import` |
| `decision` imports `connectors` | `forbidden_import` |
| `risk` imports `connectors` | `forbidden_import` |
| `dashboard` imports pipeline layers | `presentation_boundary` |
| `api` imports `research` | `forbidden_import` |
| production imports `research` | `research_isolation` (Rule R9) |

## Connector Boundaries (Rules R3, R10)

- `models/`, `config/`, governance packages must not import `connectors/`
- `connectors/` must not import intelligence or service layers
- `connectors/registry.py` must not contain market-specific branching

## Research Isolation (Rule R9)

- Production packages must not import `research/`
- `research/` may only import `models/` and stdlib-style modules
- `PromotionGate` remains interface-only

## Legacy Exclusions

Pre-Phase-0 modules are excluded until migration completes:

- `main.py`, `dashboard.py`, `config.py`
- `core/` (legacy)
- `connectors/binance_connector.py`, `connectors/psx_connector.py`

## Import Linter

Declarative forbidden-import contracts in `pyproject.toml`:

- Foundation packages must not import `connectors`
- Production must not import `research`
- Connectors must not import intelligence layers

Pipeline layer direction is enforced by the AST validator until all pipeline packages exist. The import-linter layers contract will activate when `data/` through `execution/` are scaffolded.

```bash
# Full architecture report
python scripts/validate_architecture.py

# Import contracts
lint-imports

# Architecture pytest suite
python -m pytest tests/architecture -m architecture -v
```

## CI

`.github/workflows/architecture.yml` fails on:

- Architecture validation script violations
- Import-linter contract violations
- Architecture pytest failures
- mypy strict failures
- ruff failures
- pytest failures (unit, contract, architecture)

## Rules Satisfied

| Rule | Coverage |
|---|---|
| R3 | No market branching in registry or services |
| R9 | Research isolation |
| R10 | Connector plugin boundaries |
| R11 | Dependency direction |
| R12 | Presentation layer boundaries |
