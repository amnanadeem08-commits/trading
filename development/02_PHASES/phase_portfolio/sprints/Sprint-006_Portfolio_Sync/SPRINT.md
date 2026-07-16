# Sprint-006 — Binance Spot Portfolio Sync and Analysis

## Goal

Augment the existing fixed crypto scan universe with non-dust Binance Spot
holdings and present a separate, advisory-only Portfolio Signals view.

## Scope

- Read-only Binance Spot balance, market metadata, and ticker gateway
- Typed portfolio holdings, warnings, and portfolio-signal contracts
- Stable fixed-watchlist plus portfolio-symbol merge
- Minimum USDT holding filter and BNSOL-to-SOL analysis mapping
- Pair existence, Spot, active, and TRADING validation
- Separate Portfolio Signals table and non-fatal warnings
- Top-level scanner controls with redundant sidebar content removed
- Focused unit, integration, and Streamlit UI tests

## Dependencies

- Existing fixed signal universe and legacy crypto scanner
- Existing signal logic and workbook export
- Binance Spot read-only API access through ccxt

## Architecture Changes

- New additive `portfolio_sync` domain package
- New read-only Binance portfolio gateway under `connectors`
- Dashboard remains an orchestration/presentation boundary
- No execution or paper-trading imports and no trading methods

## Files Created

- `portfolio_sync/`
- `connectors/binance_spot_portfolio.py`
- `config/portfolio_sync.yaml`
- `tests/portfolio_sync/`
- `tests/integration/test_portfolio_scanner_integration.py`

## Files Modified

- `main.py`, `dashboard.py`, `config/settings.py`, `.env.example`
- Package/import-linter configuration
- Current TIOS status documents

## Tests

- Holdings-to-symbol mapping, market validation, dust filtering, deduplication
- Account/ticker/timeout/auth failure degradation
- BTC/ETH/BNB and BNSOL acceptance paths
- Scanner integration and Portfolio Signals projection
- Relocated dashboard controls and separate portfolio presentation

## Validation

- Targeted PORTFOLIO-001 tests first
- Package coverage at least 88%
- TIOS-required architecture, sync, and validation gates

## Acceptance Criteria

- [x] Existing fixed scanner remains operational and unchanged by default
- [x] Valid non-dust Spot holdings augment the crypto scan universe
- [x] BNSOL uses SOL/USDT analysis while retaining its asset identity
- [x] Portfolio failures never crash the scanner or dashboard
- [x] Portfolio Signals remain separate and advisory-only
- [x] Working sidebar controls are relocated before redundant sidebar removal
- [x] Tests and TIOS documents are synchronized

## Future Impact

- Cost-basis reconstruction and order execution remain out of scope.

## Completion Report

See `PORTFOLIO-001_COMPLETION_REPORT.md`.
