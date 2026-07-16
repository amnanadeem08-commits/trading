"""Portfolio stage message and service edge-case tests."""

from __future__ import annotations

from config.settings import PortfolioSyncSettings
from connectors.binance_spot_portfolio import (
    MarketEligibility,
    PortfolioGatewayError,
    PortfolioTimeoutError,
    SpotBalance,
)
from portfolio_sync import PortfolioSyncService, PortfolioWarningCode
from portfolio_sync.contracts import (
    PortfolioAuthenticationStatus,
    PortfolioSyncDiagnostics,
    PortfolioSyncResult,
    PortfolioWarning,
)
from portfolio_sync.service import portfolio_stage_message


class FakeGateway:
    def __init__(
        self,
        balances: tuple[SpotBalance, ...],
        prices: dict[str, float],
        eligibility: dict[str, MarketEligibility] | None = None,
        *,
        validate_errors: dict[str, Exception] | None = None,
    ) -> None:
        self.balances = balances
        self.prices = prices
        self.eligibility = eligibility or {}
        self.validate_errors = validate_errors or {}

    def fetch_balances(self) -> tuple[SpotBalance, ...]:
        return self.balances

    def validate_spot_market(self, symbol: str) -> MarketEligibility:
        if symbol in self.validate_errors:
            raise self.validate_errors[symbol]
        return self.eligibility.get(
            symbol,
            MarketEligibility(
                symbol=symbol,
                eligible=symbol in self.prices,
                reason=None if symbol in self.prices else "missing_pair",
            ),
        )

    def fetch_prices(self, symbols: tuple[str, ...]) -> dict[str, float]:
        return {symbol: self.prices[symbol] for symbol in symbols if symbol in self.prices}


def test_portfolio_stage_messages_report_exact_failure_stages() -> None:
    assert (
        portfolio_stage_message(
            PortfolioSyncResult(
                diagnostics=PortfolioSyncDiagnostics(
                    portfolio_sync_enabled=True,
                    credentials_loaded=False,
                )
            )
        )
        == "Binance credentials were not loaded."
    )
    assert (
        portfolio_stage_message(
            PortfolioSyncResult(
                warnings=(
                    PortfolioWarning(
                        code=PortfolioWarningCode.AUTHENTICATION_FAILED,
                        message="Binance authentication failed: denied",
                    ),
                ),
                diagnostics=PortfolioSyncDiagnostics(
                    portfolio_sync_enabled=True,
                    credentials_loaded=True,
                    authentication_status=PortfolioAuthenticationStatus.FAILED,
                ),
            )
        )
        == "Binance authentication failed: denied"
    )
    valuation_failed = PortfolioSyncResult(
        diagnostics=PortfolioSyncDiagnostics(
            portfolio_sync_enabled=True,
            credentials_loaded=True,
            fetch_balance_executed=True,
            fetch_balance_success=True,
            non_zero_balance_count=4,
            valid_market_count=4,
            successfully_valued_count=0,
        )
    )
    assert (
        portfolio_stage_message(valuation_failed)
        == "4 non-zero assets found, but ticker valuation failed."
    )
    below_threshold = PortfolioSyncResult(
        diagnostics=PortfolioSyncDiagnostics(
            portfolio_sync_enabled=True,
            credentials_loaded=True,
            fetch_balance_executed=True,
            fetch_balance_success=True,
            non_zero_balance_count=4,
            successfully_valued_count=4,
            above_threshold_count=0,
            final_holding_count=0,
        )
    )
    assert (
        portfolio_stage_message(below_threshold)
        == "4 assets found; 4 were below the configured threshold."
    )
    assert (
        portfolio_stage_message(
            PortfolioSyncResult(
                warnings=(
                    PortfolioWarning(
                        code=PortfolioWarningCode.API_TIMEOUT,
                        message="Portfolio sync timed out; showing last cached result.",
                    ),
                ),
                diagnostics=PortfolioSyncDiagnostics(
                    portfolio_sync_enabled=True,
                    credentials_loaded=True,
                ),
            ),
            from_cache=True,
        )
        == "Portfolio sync timed out; showing last cached result."
    )
    assert (
        portfolio_stage_message(
            PortfolioSyncResult(
                    diagnostics=PortfolioSyncDiagnostics(
                        portfolio_sync_enabled=True,
                        credentials_loaded=True,
                        fetch_balance_executed=True,
                        fetch_balance_success=True,
                        non_zero_balance_count=3,
                        valid_market_count=0,
                        successfully_valued_count=0,
                        above_threshold_count=0,
                        final_holding_count=0,
                    )
            )
        )
        == "3 assets found; 3 were removed by market validation or dust filtering."
    )


def test_account_unavailable_during_market_validation_is_warning() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("BTC", 1.0, 0.0),),
        prices={"BTC/USDT": 100.0},
        validate_errors={"BTC/USDT": PortfolioGatewayError("markets unavailable")},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(enabled=True, minimum_holding_usdt=1.0),
    ).sync()
    assert result.holdings == ()
    assert result.warnings[0].code == PortfolioWarningCode.ACCOUNT_UNAVAILABLE


def test_sync_result_sync_succeeded_property() -> None:
    success = PortfolioSyncResult(
        diagnostics=PortfolioSyncDiagnostics(
            fetch_balance_success=True,
            authentication_status=PortfolioAuthenticationStatus.SUCCESS,
        )
    )
    failure = PortfolioSyncResult(
        diagnostics=PortfolioSyncDiagnostics(fetch_balance_executed=True)
    )
    assert success.sync_succeeded is True
    assert failure.sync_succeeded is False


def test_validate_and_batch_price_errors_become_warnings() -> None:
    gateway = FakeGateway(
        balances=(
            SpotBalance("BTC", 1.0, 0.0),
            SpotBalance("ETH", 1.0, 0.0),
        ),
        prices={"BTC/USDT": 100.0},
        validate_errors={"ETH/USDT": PortfolioTimeoutError("market timeout")},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(enabled=True, minimum_holding_usdt=1.0),
    ).sync()
    assert result.holdings[0].asset == "BTC"
    assert any(warning.code == PortfolioWarningCode.API_TIMEOUT for warning in result.warnings)

    batch_failure = FakeGateway(
        balances=(SpotBalance("BTC", 1.0, 0.0),),
        prices={"BTC/USDT": 100.0},
    )

    def raise_batch(_symbols: tuple[str, ...]) -> dict[str, float]:
        raise PortfolioGatewayError("batch ticker failed")

    batch_failure.fetch_prices = raise_batch  # type: ignore[method-assign]
    failed = PortfolioSyncService(
        batch_failure,
        PortfolioSyncSettings(enabled=True, minimum_holding_usdt=1.0),
    ).sync()
    assert failed.holdings == ()
    assert failed.warnings[0].code == PortfolioWarningCode.PRICE_UNAVAILABLE
