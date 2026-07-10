# Phase Gate

## Phase 0 Gate

Phase 0 is complete when all gate criteria pass:

| Criterion | Validator |
|---|---|
| Architecture validation | `scripts/validate_architecture.py` |
| Import-linter | `lint-imports` / Phase 0 gate |
| mypy strict | `scripts/dev.py typecheck` |
| Ruff | `scripts/dev.py lint` |
| Black | `scripts/dev.py format` |
| Pytest | `scripts/dev.py test` |
| Coverage >= 88% | `scripts/dev.py coverage` |
| Configuration | `scripts/validate_configuration.py` |
| Environment | `scripts/validate_environment.py` |
| Documentation | Phase 0 gate |
| No TODOs / hacks | Phase 0 gate |

## One-Command Validation

```bash
python scripts/validate_phase0.py
```

Generates `PHASE0_CERTIFICATION.md` with pass/fail status.

## Architecture Freeze v1.0

The following are **frozen** as of Phase 0 completion:

- `models/`
- `config/`
- `events/`
- `versioning/`
- `audit/`
- `feature_flags/`
- `connectors/base.py`

### Change Process

1. Submit an **Architecture Change Proposal (ACP)**
2. Document breaking vs non-breaking impact
3. Increment schema/version for breaking changes
4. Include migration path
5. Obtain explicit approval before implementation

## Phase 1 Authorization

Phase 1 must not begin until:

1. `PHASE0_CERTIFICATION.md` shows **CERTIFIED**
2. Explicit authorization is granted
3. ACP process is acknowledged for frozen packages
