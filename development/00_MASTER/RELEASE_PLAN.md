# Release Plan

**Last updated:** 2026-07-11

## Principles

1. No release without all TIOS validation gates passing.
2. Frozen public APIs require an Architecture Change Proposal (ACP).
3. Broker automation and autonomous execution remain disabled until an explicit approved release document says otherwise.
4. TIOS docs (`CHANGELOG`, `PROJECT_STATUS`, sprint completion) update with every release candidate.

## Existing Tooling

| Step | Command / artifact |
|------|--------------------|
| Dev commands | `python scripts/dev.py` |
| Architecture | `python scripts/validate_architecture.py` |
| Configuration | `python scripts/validate_configuration.py` |
| Dependencies | `python scripts/validate_dependencies.py` |
| Phase 0 gate | `python scripts/validate_phase0.py` → `PHASE0_CERTIFICATION.md` |
| Foundation gate | `python scripts/foundation_certification.py` → `FOUNDATION_CERTIFICATION.md` |
| Release runner | `python scripts/release.py` / `scripts/validate_release.py` |
| Process doc | `docs/development/release_process.md` |
| CI | `.github/workflows/release.yml` and quality workflows |

## Planned Product Releases (Placeholders)

| Version | Theme | Gate extras |
|---------|-------|-------------|
| V1.0 | Signal Engine | **Accepted** — lifecycle docs + E2E green |
| V1.1 | Backtesting | Replay/historical validation |
| V1.2 | Paper Trading | Paper connector path + risk checks |
| V1.3 | AI Validation Loop | Validation pipeline gates |
| V1.4 | Portfolio Analytics | Portfolio lifecycle docs |
| V1.5 | Broker Integrations | Explicit human approval; flags off by default |
| V2.0 | Autonomous platform | Full safety review; not authorized now |

## TIOS Release Checklist

- [x] Active sprint completion report closed (Signal Engine V1.0 path)
- [x] `PROJECT_STATUS.md` updated
- [x] `CHANGELOG.md` updated
- [x] `TECHNICAL_DEBT.md` reviewed for paper-trading handoff
- [x] Gates in `../05_VALIDATION/GATES.md` pass for signal path
- [x] No new forbidden imports
- [x] Coverage still ≥ 88%
- [x] No live broker path enabled without approval
- [x] Next product sprint opened only via NEXT_TASK (**PAPER-001** / Sprint-002)

## Current Release Posture

Platform baseline is certified Foundation + Phase 2 ML + **Signal Engine V1.0 path accepted**.  
Broker automation remains disabled. Next recommended product work: paper trading planning (V1.2).
