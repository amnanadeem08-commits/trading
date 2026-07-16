# Project Status

**Last updated:** 2026-07-16
**Control system:** TIOS

## Snapshot

| Field | Value |
|-------|--------|
| Product | Khaldun Trade |
| Current version (platform baseline) | Foundation + Phase 2 ML + Signal Engine V1.0 + Paper Trading V1.2 + Backtesting V1 + Prediction Validation foundation |
| Product version target | V1.4 Portfolio Analytics foundation delivered |
| Current sprint | Sprint-006 — Binance Spot Portfolio Sync and Analysis (**PORTFOLIO-001 complete**) |
| Current task | — |
| Task status | — |
| Previous task | VALIDATION-001 (**complete**) |
| Current milestone | Read-only Binance Spot portfolio analysis **delivered** |
| Coverage gate | ≥ 88% |
| Broker automation | Disabled |
| Signal Engine | V1.0 path **accepted** |
| Paper Trading | V1.2 path **accepted** |
| Backtesting | V1 path **accepted** |
| Prediction Validation | Foundation **delivered** (VALIDATION-001) |
| Strategy Builder foundation | 100% (STRATEGY-001 complete) |
| Portfolio Analytics foundation | 100% (PORTFOLIO-001 complete) |
| Signal universe | 20 crypto + 20 PSX + all PMEX instruments (`signal_universe.yaml`) |

## Progress (Roadmap View)

| Area | Completed % | Notes |
|------|-------------|-------|
| Signal Engine V1.0 implementation | 100% | SIG-001…008 done |
| Paper Trading V1.2 | 100% | PAPER-001…007 done; V1.2 accepted |
| Backtesting V1 | 100% | BACKTEST-001…003 done; V1 accepted |
| Prediction Validation foundation | 100% | VALIDATION-001 done |
| Broker | disabled | V1.5 gated |

## Next Sprint / Task

**Active coding task: none** — see [`NEXT_TASK.md`](NEXT_TASK.md).

## Sync Rule

```bash
python scripts/sync_tios_status.py
python scripts/validate_tios.py
```
