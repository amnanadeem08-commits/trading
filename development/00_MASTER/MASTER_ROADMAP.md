# Master Roadmap

**Product:** Khaldun Trade  
**Control system:** TIOS  
**Last updated:** 2026-07-16

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
| Current sprint | Sprint-006 — Binance Spot Portfolio Sync and Analysis (**PORTFOLIO-001 complete**) |
| Active coding task | **none** |
| Prior implementation | PORTFOLIO-001 complete; STRATEGY-001 complete; VALIDATION-001 complete; BACKTEST-001…003 complete; PAPER-001…007 complete; Signal Engine V1.0 accepted |
| Prior sprint | Sprint-001 — Signal Engine (**complete**) |
| Rule | Never implement features outside the active task in NEXT_TASK.md; do not invent tasks when none |

## Product Versions (Future — Document Only Until Active Sprint)

| Version | Name | Status |
|---------|------|--------|
| V1.0 | Signal Engine | **Accepted** (SIG-001…008) |
| V1.1 | Backtesting | **Accepted** (BACKTEST-001…003) |
| V1.2 | Paper Trading | **Accepted** (PAPER-001…007) |
| V1.3 | AI Validation Loop | **Foundation delivered** (VALIDATION-001) |
| Strategy Builder | Deterministic rule foundation | **Complete** (STRATEGY-001) |
| V1.4 | Portfolio Analytics | **Foundation delivered** (PORTFOLIO-001) |
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
