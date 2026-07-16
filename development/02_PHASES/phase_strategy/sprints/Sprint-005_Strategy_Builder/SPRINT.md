# Sprint-005 — Deterministic Strategy Builder

## Goal

Deliver an auditable deterministic foundation for defining and evaluating
rule-based trading strategies from an explicitly approved indicator set.

## Scope

- Typed strategy, rule, indicator, and risk-reference contracts
- Deterministic validation, identity, serialization, and registry behavior
- Current-candle-only rule and indicator evaluation
- BUY, SELL, HOLD, and EXIT outcomes with rule-level explanations
- Example strategies and a narrow Backtesting V1 signal-boundary adapter
- Focused acceptance and integration tests

## Dependencies

- Signal Engine V1.0 (accepted)
- Backtesting V1 (accepted; engine remains unchanged)
- Shared market-data, decision, signal, and risk contracts

## Architecture Changes

- New additive `strategy_builder` package
- Core package depends only on shared contracts and deterministic indicator utilities
- Backtesting compatibility is isolated in an adapter
- No imports from execution, connectors, paper trading, AI, or ML packages

## Files Created

- `strategy_builder/`
- `tests/strategy_builder/`
- `tests/integration/test_strategy_backtesting_adapter.py`
- `development/02_PHASES/phase_strategy/`

## Files Modified

- Package and import-linter configuration
- Current TIOS status documents

## Tests

- Contract and dependency validation
- Rule-group and crossing semantics
- Insufficient-data and no-look-ahead behavior
- Deterministic identity, serialization, and registry behavior
- BUY, SELL, HOLD, and EXIT outcomes
- Backtesting signal-boundary compatibility

## Validation

- Targeted STRATEGY-001 tests first
- Package coverage at least 88%
- Full TIOS-required gates

## Acceptance Criteria

- [x] Strategy and rule contracts cover the approved deterministic scope
- [x] Unknown indicators and invalid dependencies fail validation
- [x] Evaluator fails closed and never consumes future candles
- [x] Registry prevents duplicate strategy versions
- [x] Example strategies and backtesting adapter are verified
- [x] TIOS documents and completion report are synchronized

## Future Impact

- STRATEGY-002, optimization, ranking, AI generation, and UI remain deferred.

## Completion Report

See `STRATEGY-001_COMPLETION_REPORT.md`.
