# Phase Backtest — V1 Backtesting

**Status:** BACKTEST-003 complete — Backtesting V1 accepted  
**Product version:** V1.1 Backtesting  
**Prerequisite:** Signal Engine V1.0 accepted; Paper Trading V1.2 accepted  
**Active phase folder:** `sprints/Sprint-003_Backtesting/`

## Purpose

Replay historical candles through existing signal and risk evaluation boundaries with deterministic, look-ahead-free trade simulation, full lifecycle audit records, and a stable reporting boundary — **no live execution, no broker automation, no dashboard UI**.

## Rules

- Implement only the task listed in `00_MASTER/NEXT_TASK.md`
- Reuse signal/risk foundation contracts; do not import `paper_trading` from `backtesting`
- Fill pricing mirrors PAPER-004 math via local adapter (see `TECHNICAL_DEBT.md`)
- No profit guarantees / financial advice framing

## Sprints

| Sprint | Status |
|--------|--------|
| [Sprint-003 Backtesting](sprints/Sprint-003_Backtesting/) | BACKTEST-001…003 complete; [V1 readiness](BACKTESTING_V1_READINESS.md) |
