# Project Structure

## Foundation Packages (Phase 0 — Frozen)

| Package | Purpose |
|---|---|
| `models/` | Shared typed contracts |
| `config/` | Pydantic settings + YAML loader |
| `connectors/` | Market plugin framework (`base.py` frozen) |
| `events/` | In-process event bus |
| `versioning/` | Version registries |
| `audit/` | Append-only audit contracts |
| `feature_flags/` | Runtime feature flags |
| `research/` | Promotion gate interface |
| `architecture/` | Architecture enforcement engine |
| `health/` | Health registry and lifecycle checks |
| `metrics/` | Metric interfaces and registry |
| `platform_logging/` | Structured logging (stdlib-safe import name) |
| `security/` | RBAC models and security interfaces |
| `notifications/` | Notification scaffolds |
| `monitoring/` | Monitoring orchestration |

## Configuration

| Path | Purpose |
|---|---|
| `config/*.yaml` | YAML configuration files |
| `config/settings.py` | Pydantic settings |
| `config/hash.py` | Configuration hash for `ReproducibilityKey` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/bootstrap.py` | Environment bootstrap |
| `scripts/dev.py` | Development commands |
| `scripts/release.py` | Release validation |
| `scripts/validate_phase0.py` | Full Phase 0 gate |
| `scripts/validate_*.py` | Individual validators |

## Tests

| Directory | Purpose |
|---|---|
| `tests/unit/` | Unit tests |
| `tests/contract/` | Contract tests |
| `tests/architecture/` | Architecture rule tests |
| `tests/integration/` | Foundation integration tests |

## Legacy (Pre-Phase 0)

| Path | Status |
|---|---|
| `main.py`, `dashboard.py`, `config.py` | Legacy — excluded from foundation gates |
| `core/` | Legacy — migration pending |
| `connectors/binance_connector.py` | Legacy — migration pending |
| `connectors/psx_connector.py` | Legacy — migration pending |

## Out of Scope (Phase 1+)

`services/`, `data/`, `core/` (new), `ml/`, `ai/`, `decision/`, `risk/`, `execution/`
