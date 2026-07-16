"""PORTFOLIO-001 synchronization acceptance tests."""

from __future__ import annotations

from config.settings import PortfolioSyncSettings
from connectors.binance_spot_portfolio import (
    MarketEligibility,
    PortfolioAuthenticationError,
    PortfolioGatewayError,
    PortfolioTimeoutError,
    SpotBalance,
)
from portfolio_sync import PortfolioSyncService, PortfolioWarningCode
from portfolio_sync.service import portfolio_stage_message


class FakeGateway:
    def __init__(
        self,
        balances: tuple[SpotBalance, ...],
        prices: dict[str, float],
        eligibility: dict[str, MarketEligibility] | None = None,
    ) -> None:
        self.balances = balances
        self.prices = prices
        self.eligibility = eligibility or {}
        self.fetch_balance_calls = 0
        self.fetch_prices_calls = 0
        self.fetch_prices_symbols: list[tuple[str, ...]] = []

    def fetch_balances(self) -> tuple[SpotBalance, ...]:
        self.fetch_balance_calls += 1
        return self.balances

    def validate_spot_market(self, symbol: str) -> MarketEligibility:
        return self.eligibility.get(
            symbol,
            MarketEligibility(
                symbol=symbol,
                eligible=symbol in self.prices,
                reason=None if symbol in self.prices else "missing_pair",
            ),
        )

    def fetch_prices(self, symbols: tuple[str, ...]) -> dict[str, float]:
        self.fetch_prices_calls += 1
        self.fetch_prices_symbols.append(symbols)
        return {symbol: self.prices[symbol] for symbol in symbols if symbol in self.prices}


def _settings(*, minimum: float = 1.0) -> PortfolioSyncSettings:
    return PortfolioSyncSettings(
        enabled=True,
        minimum_holding_usdt=minimum,
        quote_asset="USDT",
        asset_analysis_mapping={"BNSOL": "SOL/USDT"},
    )


def test_btc_eth_and_bnb_holdings_are_synchronized() -> None:
    gateway = FakeGateway(
        balances=(
            SpotBalance("BTC", 0.01, 0.0),
            SpotBalance("ETH", 0.2, 0.0),
            SpotBalance("BNB", 1.0, 0.0),
        ),
        prices={"BTC/USDT": 60_000.0, "ETH/USDT": 3_000.0, "BNB/USDT": 500.0},
    )
    result = PortfolioSyncService(gateway, _settings()).sync()
    assert tuple(holding.asset for holding in result.holdings) == ("BTC", "ETH", "BNB")
    assert result.portfolio_symbols == ("BTC/USDT", "ETH/USDT", "BNB/USDT")
    assert result.diagnostics.binance_connected
    assert result.diagnostics.non_zero_balance_count == 3
    assert result.diagnostics.valid_market_count == 3
    assert result.diagnostics.above_threshold_count == 3
    assert result.diagnostics.final_holding_count == 3
    assert gateway.fetch_balance_calls == 1
    assert gateway.fetch_prices_calls == 1


def test_bnsol_uses_sol_analysis_and_keeps_original_asset() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("BNSOL", 2.0, 0.0),),
        prices={"SOL/USDT": 150.0},
    )
    result = PortfolioSyncService(gateway, _settings()).sync()
    holding = result.holdings[0]
    assert holding.asset == "BNSOL"
    assert holding.scan_symbol == "SOL/USDT"
    assert holding.analysis_symbol == "SOLUSDT"
    assert holding.analysis_explanation == "Market analysis is based on SOL/USDT."
    assert result.diagnostics.mapped_asset_count == 1


def test_dust_below_one_usdt_is_ignored_but_threshold_is_included() -> None:
    gateway = FakeGateway(
        balances=(
            SpotBalance("BTC", 0.00001, 0.0),
            SpotBalance("ETH", 0.001, 0.0),
        ),
        prices={"BTC/USDT": 50_000.0, "ETH/USDT": 1_000.0},
    )
    result = PortfolioSyncService(gateway, _settings()).sync()
    assert tuple(holding.asset for holding in result.holdings) == ("ETH",)
    assert result.holdings[0].current_value_usdt == 1.0
    assert any(warning.code == PortfolioWarningCode.DUST_BALANCE for warning in result.warnings)


def test_invalid_pair_is_warning_not_failure() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("RESTRICTED", 5.0, 0.0),),
        prices={},
        eligibility={
            "RESTRICTED/USDT": MarketEligibility(
                symbol="RESTRICTED/USDT",
                eligible=False,
                reason="restricted_asset",
            )
        },
    )
    result = PortfolioSyncService(gateway, _settings()).sync()
    assert result.holdings == ()
    assert result.warnings[0].code == PortfolioWarningCode.RESTRICTED_ASSET


class FailingGateway(FakeGateway):
    def fetch_balances(self) -> tuple[SpotBalance, ...]:
        raise PortfolioGatewayError("account unavailable")


class TimeoutGateway(FakeGateway):
    def fetch_balances(self) -> tuple[SpotBalance, ...]:
        raise PortfolioTimeoutError("timed out")


def test_api_failures_do_not_escape_service() -> None:
    failed = PortfolioSyncService(FailingGateway((), {}), _settings()).sync()
    timed_out = PortfolioSyncService(TimeoutGateway((), {}), _settings()).sync()
    assert failed.warnings[0].code == PortfolioWarningCode.ACCOUNT_UNAVAILABLE
    assert timed_out.warnings[0].code == PortfolioWarningCode.API_TIMEOUT


def test_disabled_zero_and_missing_pair_paths_fail_softly() -> None:
    disabled = PortfolioSyncService(
        FakeGateway((), {}),
        PortfolioSyncSettings(enabled=False),
    ).sync()
    assert disabled.holdings == ()
    assert disabled.warnings == ()

    gateway = FakeGateway(
        balances=(
            SpotBalance("ZERO", 0.0, 0.0),
            SpotBalance("MISSING", 1.0, 0.0),
        ),
        prices={},
    )
    result = PortfolioSyncService(gateway, _settings()).sync()
    assert {warning.code for warning in result.warnings} == {
        PortfolioWarningCode.ZERO_BALANCE,
        PortfolioWarningCode.MISSING_PAIR,
    }


class AuthenticationGateway(FakeGateway):
    def fetch_balances(self) -> tuple[SpotBalance, ...]:
        raise PortfolioAuthenticationError("invalid credentials")


class PriceFailureGateway(FakeGateway):
    def fetch_prices(self, symbols: tuple[str, ...]) -> dict[str, float]:
        raise PortfolioGatewayError("batch ticker failed")


def test_authentication_and_price_failures_become_warnings() -> None:
    authentication = PortfolioSyncService(
        AuthenticationGateway((), {}),
        _settings(),
    ).sync()
    price_failure = PortfolioSyncService(
        PriceFailureGateway(
            (SpotBalance("BTC", 1.0, 0.0),),
            {"BTC/USDT": 1.0},
        ),
        _settings(),
    ).sync()
    assert authentication.warnings[0].code == PortfolioWarningCode.AUTHENTICATION_FAILED
    assert authentication.diagnostics.authentication_status.value == "failed"
    assert price_failure.warnings[0].code == PortfolioWarningCode.PRICE_UNAVAILABLE
    assert "non-zero assets found" in portfolio_stage_message(price_failure)


def test_quote_asset_is_reported_as_an_explicit_filter_reason() -> None:
    result = PortfolioSyncService(
        FakeGateway((SpotBalance("USDT", 25.0, 0.0),), {}),
        _settings(),
    ).sync()
    assert result.holdings == ()
    assert result.diagnostics.non_zero_balance_count == 1
    assert result.diagnostics.valid_market_count == 0
    assert result.warnings[0].code == PortfolioWarningCode.QUOTE_ASSET


def test_representative_ccxt_balance_fixture_includes_major_holdings() -> None:
    gateway = FakeGateway(
        balances=(
            SpotBalance("BTC", 0.01, 0.0),
            SpotBalance("ETH", 0.2, 0.0),
            SpotBalance("BNB", 1.0, 0.0),
            SpotBalance("BNSOL", 2.0, 0.0),
            SpotBalance("USDT", 25.0, 0.0),
        ),
        prices={
            "BTC/USDT": 60_000.0,
            "ETH/USDT": 3_000.0,
            "BNB/USDT": 500.0,
            "SOL/USDT": 150.0,
        },
    )
    result = PortfolioSyncService(gateway, _settings()).sync()
    assert tuple(holding.asset for holding in result.holdings) == (
        "BTC",
        "ETH",
        "BNB",
        "BNSOL",
    )
    bnsol = next(holding for holding in result.holdings if holding.asset == "BNSOL")
    assert bnsol.scan_symbol == "SOL/USDT"
    assert gateway.fetch_prices_calls == 1
    assert gateway.fetch_prices_symbols[0] == (
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT",
        "SOL/USDT",
    )
