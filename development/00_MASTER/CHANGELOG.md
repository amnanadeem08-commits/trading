# Changelog

All notable TIOS and platform milestones are recorded here. Historical certification files remain authoritative for their gates.

## 2026-07-16 — VALIDATION-001 Prediction Outcome Validation Foundation

### Added

- `prediction_validation/` — prediction/outcome contracts, append-only store, evaluator, metrics, service
- `tests/prediction_validation/` — acceptance tests + fixtures
- `tests/integration/test_prediction_validation_e2e.py` — record/evaluate/summarize E2E
- `development/02_PHASES/phase_validation/` — sprint-004 task and completion report

### Changed

- `pyproject.toml` — `prediction_validation` package, coverage, import-linter contract
- NEXT_TASK → **none** (prediction validation foundation delivered)

### Notes

- Reuses `models` and `market_data` contracts; no `paper_trading`, `backtesting`, or broker imports
- No ML retraining, optimization, dashboard UI, or VALIDATION-002 work

## 2026-07-16 — BACKTEST-003 Backtesting Results, Acceptance, and Reporting

### Added

- `BacktestReport` contract with strategy/risk/simulation config references, warnings, technical notes
- `backtesting/reporting/` — `build_backtest_report`, JSON serializer, human-readable summary
- `tests/backtesting/test_reporting.py` — acceptance fixture tests (profitable, losing, no-trade, rejected, determinism, serialization, metrics)
- `development/02_PHASES/phase_backtest/BACKTESTING_V1_READINESS.md` — V1 acceptance checklist
- `development/02_PHASES/phase_backtest/sprints/Sprint-003_Backtesting/TASK-BACKTEST-003.md`

### Changed

- `backtesting/__init__.py` exports reporting APIs
- NEXT_TASK → **none** (Backtesting V1 accepted)

### Notes

- TD-BT-01/02 unchanged (documented in report technical notes)
- No UI, optimization, AI validation, or broker work

## 2026-07-16 — BACKTEST-002 Historical Signal Replay and Trade Lifecycle

### Added

- `BacktestTradeLifecycle` enum and risk verdict fields on `BacktestTradeResult`
- Full lifecycle replay: rejected, stop-loss, take-profit, signal exit, end-of-data
- `tests/backtesting/test_trade_lifecycle.py`, `test_pricing_compatibility.py`
- `development/02_PHASES/phase_backtest/sprints/Sprint-003_Backtesting/TASK-BACKTEST-002.md`

### Changed

- `BacktestRunner` records risk rejections and signal invalidation exits
- `BacktestSummary.rejected_trades` metric; closed-trade P&L excludes rejected records
- NEXT_TASK → **none** (Backtesting V1.1 lifecycle replay delivered)

### Notes

- Default bps/cash/quantity parity with paper `FillConfig` verified; `fill_fraction` paper-only (TD-BT-02)
- TD-BT-01 unchanged (local pricing adapter)
- No BACKTEST-003, AI validation, or broker work

## 2026-07-16 — BACKTEST-001 Deterministic Backtesting Foundation

### Added

- `backtesting/` package — request/config/trade/run/summary contracts, `BacktestRunner`, `ChronologicalCandleFeed`
- `tests/backtesting/` — unit tests for feed, metrics, runner, deterministic IDs
- `tests/integration/test_backtesting_e2e.py` — E2E replay, look-ahead guard, reproducibility
- `development/02_PHASES/phase_backtest/` — sprint-003 task and completion report

### Changed

- `pyproject.toml` — `backtesting` package, coverage, import-linter contract
- NEXT_TASK → **none** (Backtesting V1.1 foundation delivered)

### Notes

- Reuses signal engine + foundation risk contracts; does not import `paper_trading`
- Fill pricing adapter documented as TD-BT-01 (mirrors PAPER-004 math locally)
- No dashboard/UI, optimization, or broker integration

## 2026-07-16 — PAPER-007 E2E Suite and V1.2 Readiness

### Added

- `paper_trading/journal/metrics.py` — deterministic `PaperPerformanceMetrics` aggregation
- `tests/integration/test_paper_trading_e2e.py` — full paper path E2E (accept/reject/cancel/open/closed)
- `tests/paper_trading/test_performance_metrics.py` — metrics unit tests
- `development/02_PHASES/phase_paper/PAPER_TRADING_V1_READINESS.md` — V1.2 acceptance checklist

### Changed

- `PaperJournalService.performance_metrics()` — dashboard-ready summary via journal service boundary
- Journal entries record optional stop/target prices from signal for risk/reward metrics
- NEXT_TASK → **none** (Paper Trading V1.2 accepted)

### Notes

- Reuses PAPER-003…006 paths; no duplicate ledger/audit/journal logic
- `live_trading_enabled` remains false; broker automation still gated (V1.5)

## 2026-07-16 — PAPER-006 Journal and Review Contracts

### Added

- `paper_trading/contracts/journal.py` — journal entry, review note, filter, summary, trade-state contracts
- `paper_trading/journal/` — append-only in-memory store + service building records from fill/risk/lifecycle outcomes
- `tests/paper_trading/test_journal.py` — journal recording, review attachment, filter/summary, idempotency tests

### Changed

- `PaperTradingOrchestrator` — records journal entries on fill, reject, risk-reject prepare, and cancel paths
- NEXT_TASK → **PAPER-007** (READY)

### Notes

- Journal text and review notes are for simulated trade review only — not financial advice
- Deterministic `journal_id` prevents duplicate records on retries; no duplicate ledger/audit logic

## 2026-07-16 — PAPER-005 Paper Lifecycle Events and Audit

### Added

- `paper_trading/lifecycle/` — deterministic domain events + deterministic, append-only audit records for paper trading lifecycle
- `tests/paper_trading/test_lifecycle.py` — emit-on-fill + emit-on-reject lifecycle tests

### Changed

- `PaperTradingOrchestrator.execute_simulated_fill` — emits lifecycle events + writes audit records for fill accepted and risk/mapping failures
- `PaperSessionRegistry.update_status` — supports PAPER-005 cancellation events without ledger/portfolio mutation

### Notes

- Paper lifecycle audit/event emission is idempotent (skips duplicates via deterministic `event_id`)
- No live execution, broker integration, futures, leverage, or fund custody added

## 2026-07-16 — PAPER-004 Simulation Fill and Position/PnL Ledger

### Added

- `paper_trading/fill/` — deterministic spread/slippage/commission engine and `SimulatedFillExecutor`
- `paper_trading/ledger/` — append-only position and PnL ledgers
- `paper_trading/portfolio/` — `PaperPortfolioManager` (cash, equity, open/closed positions)
- Contracts: `SimulatedFill`, `PositionLedgerEntry`, `PnLLedgerEntry`, `PaperPortfolioState`, `PaperFillResult`
- `execute_simulated_fill` on paper orchestrator (signal → risk gate → fill → ledgers → session)
- Fill config in `config/paper_trading.yaml` / `PaperTradingSettings`
- Unit + integration tests (`test_fill_engine`, `test_ledger`, `test_fill_integration`)

### Changed

- `PaperSessionStatus` extended with `FILLED`, `PARTIALLY_FILLED`, `CANCELLED`
- NEXT_TASK → **PAPER-005** (READY)

### Notes

- Simulated PnL is for learning/review only — not guaranteed returns
- No live settlement or broker reconciliation

## 2026-07-12 — Full universe + PMEX market (config/dashboard)

### Changed

- Scan path uses full `signal_universe.yaml` lists (20 crypto, 20 PSX); removed `TOP_N` / volume-rank helpers from the legacy scan path
- PMEX enabled as third market: all configured instruments (7) via `connectors/pmex_connector.py`
- Dashboard markets: Crypto, PSX, PMEX, Both, All Markets

## 2026-07-12 — Signal universe expansion (config only)

### Changed

- `config/signal_universe.yaml`: 20 crypto + 20 PSX symbols (no PMEX)
- Duplicate symbol detection after normalization in `core/signal_universe.py`
- Dashboard Assets metric / sidebar show configured monitored universe counts

## 2026-07-11 — PAPER-003 Risk Gate Before Simulated Fill

### Added

- `paper_trading/risk` gate binder using `RiskVerdict` / `RiskResult` (fail closed)
- `authorize_fill` / `prepare_with_risk_gate` on paper orchestrator
- `PaperRiskRejectedError` with recorded rejection reasons
- Unit + integration tests for approve/reject paths

### Changed

- `risk_gate_required_before_fill` in `config/paper_trading.yaml`
- NEXT_TASK → **PAPER-004** (READY)

### Notes

- Risk gate approval is not a profit-protection guarantee
- No simulated fill/ledger yet (PAPER-004)

## 2026-07-11 — PAPER-002 Signal → Paper Order Mapping

### Added

- `paper_trading/mapping` signal→`PaperOrderRequest` mapper with explicit reject reasons
- Adapter context bridge for paper path (`live_broker=false`)
- Directional orders require market-context reference price (no invented prices)

### Changed

- NEXT_TASK → **PAPER-003** (READY)

## 2026-07-11 — PAPER-001 Paper Trading Skeleton

### Added

- `paper_trading` package (orchestrator, session registry, contracts)
- `config/paper_trading.yaml`; pipeline layer `PAPER_TRADING` (22)
- Live-trading refusal guard on paper path

### Changed

- NEXT_TASK → **PAPER-002** (READY)

## 2026-07-11 — PAPER-PLAN-001 Paper Trading Planning

### Added

- `development/02_PHASES/phase_paper/` + Sprint-002 planning package
- Tasks PAPER-PLAN-001 and PAPER-001…PAPER-007
- TIOS phase allowlist for `phase_paper`

### Changed

- NEXT_TASK → **PAPER-001** (READY)
- Signal Engine V1.0 remains accepted; broker still disabled

## 2026-07-11 — SIG-008 E2E + Signal Engine V1.0 Readiness

### Added

- `tests/integration/test_signal_engine_e2e.py` (intake→assemble→validate→event)
- `development/02_PHASES/phase_signal/SIGNAL_ENGINE_V1_READINESS.md`

### Changed

- Signal Engine V1.0 path **accepted**
- NEXT_TASK → **none** (then paper planning opened)
- Broker / live trading remain disabled

## 2026-07-11 — SIG-007 Validation / Registry / Lifecycle Events

### Added

- `signal_engine/validation` accept/reject validator with explicit reasons
- `SignalLifecycleService` — validate → register → `PredictionCreatedEvent` + audit
- Rejection emits `VALIDATION_COMPLETED` payload; no silent drops

### Changed

- NEXT_TASK → **SIG-008** (READY)

## 2026-07-11 — SIG-006 Confidence / Risk / Invalidation Binding

### Added

- `signal_engine/risk` binders for confidence, `RiskAssessment`, and `InvalidationRule`
- Structure/ATR invalidation builders, `compute_atr`, stub provider
- Explicit directional confidence rules (confidence ≠ profit probability)

### Changed

- NEXT_TASK → **SIG-007** (READY)

## 2026-07-11 — SIG-005 LLM Insight Attachment

### Added

- `signal_engine/llm` mapper from `ai` LLM/prompt contracts
- `attach_llm_insight`, provider port, stub provider, forbidden-phrase safety
- provenance `prompt_version` sync for AI-enhanced path

### Changed

- NEXT_TASK → **SIG-006** (READY)

## 2026-07-11 — SIG-004 ML Prediction Attachment

### Added

- `signal_engine/ml` mapper from inference normalized output / `InferenceExecutionResponse`
- `attach_ml_prediction`, provider port, stub provider, explicit failure errors

### Changed

- NEXT_TASK → **SIG-005** (READY)

## 2026-07-11 — SIG-003 Indicator/Rule Candidates

### Added

- Typed RSI/MACD/SMA + `RSIMACDRule` + `apply_candidate`

## 2026-07-11 — SIG-002 Market/Feature Intake

### Added

- `signal_engine/intake/` mappers + provenance builder

## 2026-07-11 — SIG-001 Signal Engine Skeleton

### Added

- `signal_engine` assembler/registry/contracts/config

## 2026-07-11 — Signal Engine Planning (Sprint-001 / SIG-PLAN-001)

### Added

- Planning package and TASK-SIG-001…008

## 2026-07-11 — TIOS Integrity Verification / Bootstrap

### Added

- TIOS `development/` SSOT, validators, Cursor workflow
- Sprint-000 TIOS Bootstrap records

## Prior Milestones (Pointers)

| Date / Tag | Milestone | Authority |
|------------|-----------|-----------|
| Foundation tag `v1.0.0-foundation` | Intelligence pipeline freeze | `FOUNDATION_CERTIFICATION.md` |
| Phase 0 | Contracts certified | `PHASE0_CERTIFICATION.md` |
| Phase 2 | ML execution | Codebase + TIOS phase doc |
