# Sprint-003 — Backtesting

## Goal

Deliver V1 deterministic backtesting with full historical signal replay, simulated trade lifecycle audit records, and stable reporting/acceptance boundary.

## Scope

- Backtest contracts (request, config, trade, run, summary)
- Chronological candle replay with look-ahead protection
- Signal engine integration (RSI/MACD statistical path)
- Risk verdict gate (foundation contracts)
- Deterministic trade simulation with fees/slippage
- Performance metrics aggregation
- Report contract, JSON serialization, human-readable summary
- Focused lifecycle, pricing compatibility, and acceptance tests

## Dependencies

- Signal Engine V1.0 (accepted)
- Paper Trading V1.2 (accepted — contracts referenced, not imported)

## Architecture Changes

- New `backtesting` package (additive)
- Import-linter contract: `backtesting` must not import `paper_trading`, `execution`, `connectors`

## Files Created

- `backtesting/` package
- `tests/backtesting/`
- `tests/integration/test_backtesting_e2e.py`

## Files Modified

- `pyproject.toml` — package, coverage, import-linter
- TIOS status docs

## Tests

- Unit: candle feed, metrics, runner, deterministic IDs
- Integration: E2E replay, look-ahead guard, reproducibility

## Validation

- Targeted pytest first
- Full TIOS gates (`validate_tios.py`)

## Acceptance Criteria

- [x] Chronological replay without look-ahead
- [x] Deterministic run/trade IDs and reproducible results
- [x] Trade records include lifecycle, risk verdict, entry/exit/stop/target/fees/slippage/PnL/return/outcome
- [x] Summary metrics: win rate, profit factor, max drawdown, average R/R, rejected trades
- [x] Auditable report contract with JSON serialization and human-readable summary
- [x] No paper_trading import from backtesting
- [x] No UI/dashboard work

## Future Impact

- Historical storage bridge, multi-symbol, and dashboard contracts remain future work
- AI validation loop (V1.3) remains out of scope

## Completion Report

See `BACKTEST-003_COMPLETION_REPORT.md` (latest). `BACKTEST-001_COMPLETION_REPORT.md` and `BACKTEST-002_COMPLETION_REPORT.md` for prior tasks.
