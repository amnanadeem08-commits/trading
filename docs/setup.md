# Setup Guide

## Prerequisites

- Python 3.14+
- Git
- pip

## Bootstrap

```bash
python scripts/bootstrap.py
```

This installs the package in editable mode with dev dependencies and runs environment, dependency, and configuration validation.

## Verify Foundation

```bash
python scripts/validate_phase0.py
```

## Development Commands

```bash
python scripts/dev.py lint
python scripts/dev.py format
python scripts/dev.py typecheck
python scripts/dev.py test
python scripts/dev.py coverage
python scripts/dev.py architecture
python scripts/dev.py phase0
```

## Pre-commit

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Docker (Scaffold)

```bash
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.test.yml run --rm platform-test
```

## Environment

Copy `.env.example` to `.env` and adjust values. See [configuration.md](configuration.md).

## Next Steps

1. Read [project_structure.md](project_structure.md)
2. Read [phase_gate.md](phase_gate.md)
3. Run Phase 0 certification before Phase 1 work
