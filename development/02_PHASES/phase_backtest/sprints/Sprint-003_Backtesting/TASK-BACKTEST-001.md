# TASK-BACKTEST-001 — Deterministic Backtesting Foundation

## Sprint

Sprint-003 — Backtesting

## Goal

Create the minimum deterministic backtesting foundation that replays historical market data through existing Khaldoon Trade signal and evaluation boundaries.

## Scope

### Implementation Scope

- Define backtest request, configuration, trade result, run result, and summary contracts
- Accept historical candles for one symbol and one timeframe
- Process candles strictly in chronological order; prevent look-ahead bias
- Reuse existing signal/risk contracts where appropriate
- Record entry, exit, stop, target, fees, slippage, P&L, return, outcome, and timestamps
- Produce deterministic run and trade identifiers
- Calculate total trades, wins/losses, win rate, gross/net P&L, fees, average return, profit factor, max drawdown, average risk/reward
- Support fixed test fixtures and reproducible results
- Keep implementation independent from Streamlit UI

## Out of Scope

- Charts or dashboard UI
- Strategy optimization, parameter search, ML training
- Live execution, futures, leverage, broker integration
- Modifying stable PAPER-003 through PAPER-007 behavior

## Dependencies

- Signal Engine V1.0 (accepted)
- Market data `Candle` contract
- Foundation `RiskVerdict` / `ExplainableSignal` contracts

## Architecture Impact

- Additive `backtesting` package
- Fill pricing adapter mirrors PAPER-004 locally (documented as technical debt)
- `backtesting` must not import `paper_trading`

## Implementation Notes

- `ChronologicalCandleFeed` blocks future-candle access
- `BacktestRunner` evaluates signals on sliding window ending at current bar only
- Stop/target exits checked on subsequent bar OHLC (stop checked before target)

## Files Expected

- `backtesting/contracts/*`
- `backtesting/engine/*`
- `tests/backtesting/*`
- `tests/integration/test_backtesting_e2e.py`

## Tests Required

- Unit + integration
- Explicit look-ahead and chronological processing tests

## Validation Gates

- Targeted pytest, then full TIOS gates

## Acceptance Criteria

- [x] Contracts defined and exported
- [x] Deterministic replay green
- [x] Metrics aggregation complete
- [x] No look-ahead in feed tests
- [x] PAPER-003…007 unchanged

## Status

**Complete** (2026-07-16)

## Completion Notes

See `BACKTEST-001_COMPLETION_REPORT.md`.
