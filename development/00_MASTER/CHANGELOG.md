# Changelog

All notable TIOS and platform milestones are recorded here. Historical certification files remain authoritative for their gates.

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
