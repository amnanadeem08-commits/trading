# Phase 0 — Foundation Contracts

**Status:** Certified  
**Authority:** `PHASE0_CERTIFICATION.md`, `docs/architecture/phase-0.md`

## Scope

Shared typed contracts and operational scaffolds:

`models`, `config`, `events`, `versioning`, `audit`, `feature_flags`, `research` (promotion gate interface only), `architecture`, `health`, `metrics`, `platform_logging`, `security`, `notifications`, `monitoring`, connector base freeze.

## Rules

- Historical certification is immutable.
- Public contract changes require ACP.
- Do not re-implement Phase 0 in product sprints.

## Validation

```bash
python scripts/validate_phase0.py
```
