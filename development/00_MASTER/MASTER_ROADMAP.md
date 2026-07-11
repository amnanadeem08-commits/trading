# Master Roadmap

**Product:** Khaldun Trade  
**Control system:** TIOS  
**Last updated:** 2026-07-11

## Completed Infrastructure (Do Not Re-implement)

| Milestone | Status | Notes |
|-----------|--------|-------|
| Phase 0 — Foundation contracts | Certified | See `PHASE0_CERTIFICATION.md`, `docs/architecture/phase-0.md` |
| Foundation v1.0.0 — Intelligence pipeline | Certified | See `FOUNDATION_CERTIFICATION.md`, `docs/architecture/foundation_freeze.md` |
| Phase 2 — ML execution platform | Complete | Storage → artifacts → adapters → inference → ML runtime |
| V1.0 — Signal Engine path | Accepted | See `02_PHASES/phase_signal/SIGNAL_ENGINE_V1_READINESS.md` |

## Active Work

| Item | Value |
|------|-------|
| Current sprint | Sprint-002 — Paper Trading Planning (**complete**); implementation at PAPER-001 |
| Active coding task | **PAPER-002** (READY) |
| Prior implementation | PAPER-001 complete; Signal Engine V1.0 accepted |
| Prior sprint | Sprint-001 — Signal Engine (**complete**) |
| Rule | Never implement features outside the active task in NEXT_TASK.md; do not invent tasks when none |

## Product Versions (Future — Document Only Until Active Sprint)

| Version | Name | Status |
|---------|------|--------|
| V1.0 | Signal Engine | **Accepted** (SIG-001…008) |
| V1.1 | Backtesting | Placeholder |
| V1.2 | Paper Trading | PAPER-001 done; **PAPER-002 READY** |
| V1.3 | AI Validation Loop | Placeholder |
| V1.4 | Portfolio Analytics | Placeholder |
| V1.5 | Broker Integrations | Placeholder — **disabled until approved** |
| V2.0 | Autonomous AI Trading Platform | Placeholder — **disabled until approved** |

## Vision Pipeline (Target Architecture)

```
Market Data
  → Historical Storage
  → Feature Engineering
  → Technical Indicators
  → Sentiment Analysis
  → Machine Learning
  → LLM Reasoning
  → Prediction Engine
  → Confidence Engine
  → Risk Engine
  → Validation Engine
  → Decision Engine
  → (Paper / gated live execution — later versions)
```

Update this diagram only when product versions change status via TIOS.
