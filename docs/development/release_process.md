# Release Process

## Versioning

Project version follows semver in `pyproject.toml`:

```
version = "MAJOR.MINOR.PATCH"
```

## Pre-Release Checklist

1. All tests pass
2. Coverage >= 88%
3. Architecture validation passes
4. No TODO/FIXME/PLACEHOLDER/HACK markers in foundation code
5. Documentation updated
6. `PHASE0_CERTIFICATION.md` regenerated

## Release Validation

```bash
python scripts/release.py
```

This runs:

1. `scripts/validate_release.py`
2. `scripts/validate_phase0.py`

## Docker Release Image (Scaffold)

```bash
docker build -f Dockerfile -t trading-platform:foundation .
```

## Architecture Freeze

Release candidates must comply with Architecture Freeze v1.0. Breaking changes to frozen packages require an ACP and version increment.

## Post-Release

1. Archive `PHASE0_CERTIFICATION.md` artifact
2. Tag release in version control
3. Obtain authorization before Phase 1 development
