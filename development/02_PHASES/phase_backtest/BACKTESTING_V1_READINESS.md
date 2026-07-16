# Backtesting V1 Readiness Checklist

**Product:** Khaldun Trade / TIOS  
**Date:** 2026-07-16  
**Result:** Ready for Backtesting V1 path acceptance (live broker still out of scope)

## Scope Accepted

| Capability | Status |
|------------|--------|
| Deterministic foundation (`BACKTEST-001`) | Done |
| Historical signal replay + trade lifecycle (`BACKTEST-002`) | Done |
| Results, acceptance, and reporting boundary (`BACKTEST-003`) | Done |

## End-to-End Path Verified

| Stage | Verified |
|-------|----------|
| Chronological candle replay (no look-ahead) | Yes |
| Signal engine integration (RSI/MACD path) | Yes |
| Risk gate before simulated entry | Yes |
| Lifecycle states: rejected, stop-loss, take-profit, signal exit, end-of-data | Yes |
| Deterministic run/trade IDs | Yes |
| Performance summary metrics | Yes |
| Auditable report contract + JSON serialization | Yes |
| Human-readable summary formatter | Yes |
| `live_trading_enabled` remains false | Yes |

## Quality Gates

| Gate | Status |
|------|--------|
| `pytest tests/backtesting` + E2E integration | Green |
| Coverage ≥ 88% on `backtesting` | Green |
| Architecture + import-linter | Green |
| TIOS `validate_tios.py` | Green |
| Broker / live trading flags | **Disabled** |

## Known Limitations (V1)

| ID | Item |
|----|------|
| TD-BT-01 | Fill pricing duplicated locally; no `paper_trading` import |
| TD-BT-02 | Backtest assumes full fill (`fill_fraction=1.0`) |
| — | Single-symbol replay only; no multi-symbol portfolio |
| — | No historical storage bridge (caller supplies candles) |
| — | No dashboard/UI, charts, or optimization |
| — | No broker automation or live execution |

## Explicitly Out of Scope (Not V1)

- Live broker automation (V1.5 — gated)
- AI validation loop (V1.3)
- Strategy optimization / parameter search
- Streamlit or rich dashboard UI
- Profit guarantees / financial advice framing

## Recommended Next Product Work

Active coding task is **none** after BACKTEST-003 close. Open the next TIOS task only via explicit `NEXT_TASK.md` handoff — do not invent IDs here.
