# TASK-PORTFOLIO-001 — Binance Spot Portfolio Sync and Analysis

## Sprint

Sprint-006 — Binance Spot Portfolio Sync and Analysis

## Goal

Add read-only Binance Spot holdings to the existing fixed crypto scan universe
and display a separate advisory Portfolio Signals analysis.

## Scope

- Fetch non-zero Spot balances and current prices through an injected gateway
- Validate that analysis pairs exist, are Spot-enabled, active, and TRADING
- Merge fixed watchlist and portfolio symbols with stable duplicate removal
- Filter holdings below configurable `minimum_holding_usdt` (default 1.0)
- Map BNSOL analysis to SOL/USDT while retaining the BNSOL label and explanation
- Produce typed portfolio rows with optional cost basis/PnL values
- Preserve current scanner logic and workbook behavior
- Add separate Portfolio Signals UI, warnings, and advisory suggested actions
- Relocate unique working sidebar controls into a top-level toolbar

## Out of Scope

- Trade-history cost-basis reconstruction
- Automatic orders, cancellation, broker automation, futures, leverage, or margin
- Paper fills, optimization, ranking, AI generation, or PORTFOLIO-002+

## Dependencies

- Existing fixed signal universe and scanner
- Binance Spot read-only API credentials
- Existing signal output and dashboard rendering

## Architecture Impact

- Additive `portfolio_sync` package above `connectors`, `models`, and `config`
- Read-only gateway under `connectors`; no execution methods
- Core portfolio services must not import Streamlit, pandas, paper trading, or execution
- Dashboard performs only orchestration and presentation

## Implementation Notes

- Internal symbols use ccxt form (`BTC/USDT`); UI analysis symbols use compact form (`BTCUSDT`).
- Portfolio sync disabled or unavailable degrades to fixed-watchlist scanning.
- Average buy price and floating PnL remain `None` when no approved source exists.
- Missing pairs, restrictions, API timeouts, and per-asset failures become warnings.
- Entry/stop/target values are never fabricated when absent from signal data.

## Files Expected

- `portfolio_sync/`, `connectors/binance_spot_portfolio.py`
- `config/portfolio_sync.yaml`, `config/settings.py`, `.env.example`
- `main.py`, `dashboard.py`, `pyproject.toml`
- `tests/portfolio_sync/`, scanner integration and dashboard tests

## Tests Required

- BTC, ETH, and BNB holdings augment scanner output
- BNSOL uses SOL/USDT analysis with original asset label
- Dust below 1 USDT is ignored
- Duplicate symbols are scanned once
- API failure does not crash the app
- Invalid/non-Spot/non-TRADING pairs are rejected
- Sidebar controls retain behavior after relocation

## Validation Gates

- Targeted PORTFOLIO-001 tests and coverage at least 88%
- Architecture and import-linter validation
- TIOS sync and validation

## Acceptance Criteria

- [x] Read-only balance sync and pair validation are implemented
- [x] Fixed and portfolio universes merge deterministically
- [x] Portfolio rows and warnings satisfy the approved contract
- [x] Existing scanner and exports remain operational
- [x] UI controls are unique, working, and not duplicated
- [x] No execution path exists
- [x] Completion report and TIOS status are synchronized

## Status

**Complete** (2026-07-16)

## Completion Notes

See `PORTFOLIO-001_COMPLETION_REPORT.md`. Targeted acceptance passed with
91.38% package/gateway coverage.
