# TASK-BACKTEST-002 — Historical Signal Replay and Trade Lifecycle

## Sprint

Sprint-003 — Backtesting

## Goal

Extend the deterministic backtesting foundation so historical candles drive existing signal and risk boundaries and produce complete simulated trade lifecycles.

## Scope

### Implementation Scope

- Replay historical candles chronologically through the existing signal adapter
- Evaluate risk decision before opening a simulated trade
- Support lifecycle states: rejected, opened (via entry), stop-loss, take-profit, signal exit, end-of-data
- Prevent look-ahead bias, overlapping positions, duplicate trade IDs within a run
- Record signal ID, risk verdict, entry/exit timestamps and prices, stop/target, fees, slippage, P&L, return %, exit reason, outcome
- Reuse BACKTEST-001 pricing and metrics boundaries
- Add compatibility tests for backtesting vs paper-trading fee/slippage assumptions
- Document pricing duplication and config divergences as technical debt (no refactor in this task)

## Out of Scope

- Strategy optimization, parameter search, ML training
- Dashboard UI, live execution, futures, leverage, broker integration
- Refactoring duplicated pricing into shared module
- BACKTEST-003+

## Dependencies

- BACKTEST-001 (complete)
- Signal Engine V1.0 (accepted)
- Paper Trading V1.2 (contracts referenced for parity tests only)

## Architecture Impact

- Additive extensions to `backtesting/contracts` and `backtesting/engine`
- `backtesting` still must not import `paper_trading`

## Implementation Notes

- `BacktestTradeLifecycle` enum on trade records
- Risk rejection recorded as lifecycle `rejected` with verdict metadata
- Exit ordering on each bar: stop-loss → signal invalidation → take-profit (no future-candle access)
- `force_reject_bar_indices` config hook for deterministic rejection tests
- Summary `rejected_trades` count separate from closed `total_trades`

## Files Expected

- `backtesting/contracts/trade.py`, `config.py`, `summary.py`
- `backtesting/engine/runner.py`, `position.py`, `risk_evaluator.py`, `metrics.py`
- `tests/backtesting/test_trade_lifecycle.py`, `test_pricing_compatibility.py`

## Tests Required

- Stop-loss before take-profit on same bar
- Signal invalidation exit
- Risk rejection recording
- End-of-data forced close
- Deterministic repeated runs
- Paper/backtest fill pricing parity

## Validation Gates

- Targeted BACKTEST-002 pytest first
- TIOS sync + validate_tios
- Backtesting package coverage ≥ 88%

## Acceptance Criteria

- [x] Full lifecycle states recorded on trade results
- [x] Risk verdict captured on all lifecycle records
- [x] No look-ahead; no overlapping positions; no duplicate trade IDs
- [x] Pricing parity tests green (defaults match; duplication documented)
- [x] PAPER-003…007 unchanged
- [x] Docs/status synced

## Status

**Complete** (2026-07-16)

## Completion Notes

See `BACKTEST-002_COMPLETION_REPORT.md`.
