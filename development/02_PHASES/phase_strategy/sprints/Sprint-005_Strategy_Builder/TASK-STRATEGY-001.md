# TASK-STRATEGY-001 — Deterministic Rule-Based Strategy Builder Foundation

## Sprint

Sprint-005 — Deterministic Strategy Builder

## Goal

Create a deterministic and auditable strategy-definition and rule-evaluation
foundation for composing trading algorithms from approved indicators and conditions.

## Scope

- Complete strategy metadata, lifecycle, risk-reference, stop, target, and indicator contracts
- Comparison rules and recursive AND/OR rule groups
- Approved OHLCV, SMA, EMA, RSI, MACD, Bollinger Bands, ATR, and volume-average indicators
- Schema, rule, and dependency validation
- Deterministic IDs/version hashes and JSON round trips
- Thread-safe strategy registry with duplicate and enable/disable behavior
- Fail-closed current-candle evaluation producing BUY, SELL, HOLD, or EXIT
- Triggered rule IDs and human-readable deterministic explanations
- Three example strategy fixtures
- Additive adapter compatible with the existing backtesting signal boundary
- Focused unit and integration tests

## Out of Scope

- Parameter optimization or brute-force combinations
- Strategy ranking or automatic AI strategy generation
- ML training or retraining
- Streamlit or other UI work
- Live order execution, futures, leverage, or broker integration
- STRATEGY-002+

## Dependencies

- Signal Engine V1.0 accepted contracts
- Backtesting V1 accepted chronological feed and signal boundary
- Shared `models`, `market_data`, and risk references

## Architecture Impact

- Additive `strategy_builder` package
- Core strategy modules must not import backtesting, paper trading, execution,
  connectors, AI, or ML packages
- Backtesting integration is isolated under `strategy_builder.adapters`
- Accepted Backtesting V1 runner remains unchanged

## Implementation Notes

- Canonical JSON and SHA-256 establish deterministic identity.
- Crossing rules compare only previous and current values.
- Disabled, invalid, or insufficient-data evaluations return an audited HOLD.
- EXIT requires an explicit open-position context.
- Mutable registry enablement state does not change immutable strategy identity.

## Files Expected

- `strategy_builder/contracts/`, `strategy_builder/indicators/`
- `strategy_builder/evaluation/`, `strategy_builder/registry.py`
- `strategy_builder/serialization.py`, `strategy_builder/adapters/`
- `tests/strategy_builder/`
- `tests/integration/test_strategy_backtesting_adapter.py`

## Tests Required

- Valid and invalid strategy schemas
- AND and OR groups
- Crossing-above and crossing-below
- Insufficient indicator history
- No-look-ahead enforcement
- Deterministic IDs and serialization
- Duplicate prevention and enable/disable behavior
- BUY, SELL, HOLD, and EXIT outcomes
- Backtesting adapter compatibility

## Validation Gates

- Targeted STRATEGY-001 pytest first
- Package coverage at least 88%
- TIOS sync and validation gates

## Acceptance Criteria

- [x] Required strategy fields and approved operators are typed and validated
- [x] Indicator dependencies and rule references are validated
- [x] Identity, serialization, and registry behavior are deterministic
- [x] Rule evaluation is explainable, fail-closed, and free of look-ahead
- [x] Examples and backtesting adapter pass focused tests
- [x] TIOS documents and completion report are synchronized

## Status

**Complete** (2026-07-16)

## Completion Notes

See `STRATEGY-001_COMPLETION_REPORT.md`. Targeted acceptance: 27 passed with
90.49% package coverage. Architecture and import-linter gates passed.
