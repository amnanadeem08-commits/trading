# TASK-BACKTEST-003 — Backtesting Results, Acceptance, and Reporting

## Sprint

Sprint-003 — Backtesting

## Goal

Complete Backtesting V1 acceptance by producing a stable, auditable result/reporting boundary over the existing deterministic replay engine.

## Scope

### Implementation Scope

- `BacktestReport` contract with config references, separated trade/rejected records, summary, warnings, notes
- Deterministic JSON serialization and deserialization
- Human-readable summary text formatter
- Acceptance tests: profitable, losing, no-trade, risk-rejected, determinism, serialization, metrics consistency
- Backtesting V1 readiness documentation

## Out of Scope

- Streamlit UI, charts, optimization, ML training, live trading, futures, leverage, broker integration
- Refactoring TD-BT-01 or TD-BT-02
- AI validation loop

## Dependencies

- BACKTEST-001 (complete)
- BACKTEST-002 (complete)

## Architecture Impact

- Additive `backtesting/contracts/report.py` and `backtesting/reporting/` package
- `backtesting` still must not import `paper_trading`

## Implementation Notes

- `BacktestReport` splits closed trades from `rejected_trades` while preserving runner `BacktestRunResult`
- Config references snapshot strategy, risk, and simulation parameters from `BacktestRequest`
- JSON serializer uses `sort_keys=True` for deterministic output; deserialize via `model_validate_json`
- Default warnings when rejections present; TD-BT-01/02 in technical notes

## Files Expected

- `backtesting/contracts/report.py`
- `backtesting/reporting/builder.py`, `serializer.py`, `summary_text.py`
- `tests/backtesting/test_reporting.py`
- `development/02_PHASES/phase_backtest/BACKTESTING_V1_READINESS.md`

## Tests Required

- Profitable fixture report
- Losing fixture report
- No-trade fixture report
- Risk-rejected fixture report
- Deterministic repeated run
- JSON serialization round-trip
- Metrics consistency with BACKTEST-001/002 engine

## Validation Gates

- Targeted BACKTEST-003 pytest first
- TIOS sync + validate_tios
- Backtesting package coverage ≥ 88%

## Acceptance Criteria

- [x] Report contract with run metadata, config refs, trades, rejected trades, summary, warnings, notes
- [x] All acceptance metrics on summary boundary
- [x] JSON-serializable deterministic output with round-trip validation
- [x] Human-readable summary service
- [x] Acceptance fixture tests green
- [x] V1 readiness documented; docs/status synced

## Status

**Complete** (2026-07-16)

## Completion Notes

See `BACKTEST-003_COMPLETION_REPORT.md`.
