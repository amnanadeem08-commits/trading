# Testing Guide

## Test Suites

| Marker | Directory | Purpose |
|---|---|---|
| `unit` | `tests/unit/` | Unit tests |
| `contract` | `tests/contract/` | Interface contracts |
| `architecture` | `tests/architecture/` | Architecture rules |
| `integration` | `tests/integration/` | Foundation integration |

## Running Tests

```bash
python scripts/dev.py test
python scripts/dev.py coverage
```

## Coverage Target

Phase 0 requires **>= 88%** coverage across foundation packages.

## Architecture Tests

```bash
python -m pytest tests/architecture -m architecture -v
python scripts/validate_architecture.py
```

## Phase 0 Gate

```bash
python scripts/validate_phase0.py
```

## CI

Separate GitHub workflows run lint, typing, architecture, tests, coverage, release, and dependency validation on every push and pull request.
