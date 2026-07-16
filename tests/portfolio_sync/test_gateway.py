"""Read-only Binance portfolio gateway tests."""

from __future__ import annotations

import pytest

from connectors.binance_spot_portfolio import (
    BinanceSpotPortfolioGateway,
    PortfolioAuthenticationError,
    PortfolioGatewayError,
    PortfolioTimeoutError,
    _parse_balances,
)


class RequestTimeoutError(Exception):
    """Fake ccxt timeout."""


class FakeExchange:
    def __init__(self) -> None:
        self.balance = {
            "free": {"BTC": 0.1, "ETH": 0.0},
            "used": {"BTC": 0.2, "ETH": 0.0},
            "total": {"BTC": 0.3, "ETH": 0.0},
        }
        self.markets = {
            "BTC/USDT": {
                "spot": True,
                "active": True,
                "info": {"status": "TRADING", "isSpotTradingAllowed": True},
            },
            "BAD/USDT": {
                "spot": True,
                "active": False,
                "info": {"status": "BREAK"},
            },
        }
        self.fetch_ticker_symbols: list[str] = []
        self.fetch_tickers_symbols: list[list[str]] = []

    def fetch_balance(self):
        return self.balance

    def load_markets(self):
        return self.markets

    def fetch_ticker(self, symbol: str):
        self.fetch_ticker_symbols.append(symbol)
        return {"last": 100.0 if symbol == "BTC/USDT" else None}

    def fetch_tickers(self, symbols: list[str] | None = None):
        self.fetch_tickers_symbols.append(list(symbols or []))
        return {symbol: {"last": 100.0} for symbol in (symbols or [])}


def test_gateway_parses_balances_and_validates_trading_market() -> None:
    gateway = BinanceSpotPortfolioGateway(FakeExchange())
    balances = gateway.fetch_balances()
    assert len(balances) == 1
    assert balances[0].asset == "BTC"
    assert balances[0].quantity == pytest.approx(0.3)
    assert gateway.validate_spot_market("BTC/USDT").eligible
    assert not gateway.validate_spot_market("BAD/USDT").eligible
    assert gateway.validate_spot_market("MISSING/USDT").reason == "missing_pair"
    assert gateway.fetch_current_price("BTC/USDT") == 100.0


def test_gateway_rejects_unavailable_price() -> None:
    gateway = BinanceSpotPortfolioGateway(FakeExchange())
    with pytest.raises(PortfolioGatewayError, match="Price unavailable"):
        gateway.fetch_current_price("BAD/USDT")


class TimeoutExchange(FakeExchange):
    def fetch_balance(self):
        raise RequestTimeoutError("timeout")


def test_gateway_translates_timeout_after_retry() -> None:
    gateway = BinanceSpotPortfolioGateway(TimeoutExchange(), max_retries=1)
    with pytest.raises(PortfolioTimeoutError):
        gateway.fetch_balances()


def test_missing_credentials_are_rejected_before_client_creation() -> None:
    with pytest.raises(PortfolioAuthenticationError, match="missing"):
        BinanceSpotPortfolioGateway.from_credentials(
            api_key="",
            api_secret="",
            timeout_milliseconds=1_000,
            max_retries=0,
        )


def test_market_restrictions_and_balance_fallbacks_are_explicit() -> None:
    exchange = FakeExchange()
    exchange.balance = {
        "free": {},
        "used": {},
        "total": {"SOL": "2", "BAD": "not-a-number"},
    }
    exchange.markets.update(
        {
            "FUTURE/USDT": {
                "spot": False,
                "active": True,
                "info": {"status": "TRADING"},
            },
            "RESTRICTED/USDT": {
                "spot": True,
                "active": True,
                "info": {"status": "TRADING", "isSpotTradingAllowed": False},
            },
            "HALTED/USDT": {
                "spot": True,
                "active": True,
                "info": {"status": "HALT"},
            },
        }
    )
    gateway = BinanceSpotPortfolioGateway(exchange)
    balance = gateway.fetch_balances()[0]
    assert balance.asset == "SOL"
    assert balance.free == 2.0
    assert gateway.validate_spot_market("FUTURE/USDT").reason == "not_spot"
    assert gateway.validate_spot_market("RESTRICTED/USDT").reason == "restricted_asset"
    assert gateway.validate_spot_market("HALTED/USDT").reason == "not_trading"


class CloseTickerExchange(FakeExchange):
    def fetch_ticker(self, symbol: str):
        return {"last": None, "close": 42.0}


def test_ticker_close_is_used_when_last_is_absent() -> None:
    gateway = BinanceSpotPortfolioGateway(CloseTickerExchange())
    assert gateway.fetch_current_price("BTC/USDT") == 42.0


class AuthenticationError(Exception):
    """Fake ccxt authentication error."""


class AuthenticationExchange(FakeExchange):
    def fetch_balance(self):
        raise AuthenticationError("denied")


def test_gateway_translates_authentication_failure() -> None:
    with pytest.raises(PortfolioAuthenticationError):
        BinanceSpotPortfolioGateway(AuthenticationExchange()).fetch_balances()


def test_load_markets_is_called_once_per_refresh() -> None:
    exchange = FakeExchange()
    gateway = BinanceSpotPortfolioGateway(exchange)
    gateway.validate_spot_market("BTC/USDT")
    gateway.validate_spot_market("BTC/USDT")
    assert gateway.load_markets_calls == 1


def test_fetch_balance_is_called_once_per_refresh() -> None:
    gateway = BinanceSpotPortfolioGateway(FakeExchange())
    gateway.fetch_balances()
    gateway.fetch_balances()
    assert gateway.fetch_balance_calls == 2


def test_fetch_prices_uses_batch_tickers_for_multiple_symbols() -> None:
    exchange = FakeExchange()
    exchange.markets.update(
        {
            "ETH/USDT": {
                "spot": True,
                "active": True,
                "info": {"status": "TRADING", "isSpotTradingAllowed": True},
            },
            "BNB/USDT": {
                "spot": True,
                "active": True,
                "info": {"status": "TRADING", "isSpotTradingAllowed": True},
            },
        }
    )
    gateway = BinanceSpotPortfolioGateway(exchange)
    prices = gateway.fetch_prices(("BTC/USDT", "ETH/USDT", "BNB/USDT"))
    assert prices == {
        "BTC/USDT": 100.0,
        "ETH/USDT": 100.0,
        "BNB/USDT": 100.0,
    }
    assert gateway.fetch_tickers_calls == 1
    assert gateway.fetch_ticker_calls == 0


def test_fetch_prices_falls_back_when_batch_returns_partial_data() -> None:
    exchange = FakeExchange()

    class PartialBatchExchange(FakeExchange):
        def fetch_tickers(self, symbols: list[str] | None = None):
            self.fetch_tickers_symbols.append(list(symbols or []))
            return {"BTC/USDT": {"last": 100.0}}

        def fetch_ticker(self, symbol: str):
            self.fetch_ticker_symbols.append(symbol)
            return {"last": 100.0}

    exchange.markets.update(
        {
            "ETH/USDT": {
                "spot": True,
                "active": True,
                "info": {"status": "TRADING", "isSpotTradingAllowed": True},
            }
        }
    )
    gateway = BinanceSpotPortfolioGateway(PartialBatchExchange())
    prices = gateway.fetch_prices(("BTC/USDT", "ETH/USDT"))
    assert prices["BTC/USDT"] == 100.0
    assert prices["ETH/USDT"] == 100.0
    assert gateway.fetch_tickers_calls == 1
    assert gateway.fetch_ticker_calls == 1


def test_fetch_prices_falls_back_to_individual_tickers_when_batch_fails() -> None:
    exchange = FakeExchange()

    class BatchFailureExchange(FakeExchange):
        def fetch_tickers(self, symbols: list[str] | None = None):
            raise RuntimeError("batch unavailable")

    gateway = BinanceSpotPortfolioGateway(BatchFailureExchange())
    prices = gateway.fetch_prices(("BTC/USDT",))
    assert prices == {"BTC/USDT": 100.0}
    assert gateway.fetch_ticker_calls == 1


def test_market_cache_reuses_metadata_within_ttl() -> None:
    exchange = FakeExchange()
    gateway = BinanceSpotPortfolioGateway(exchange)
    gateway.ensure_markets_loaded()
    assert gateway.load_markets_calls == 1
    gateway_two = BinanceSpotPortfolioGateway(exchange)
    gateway_two.ensure_markets_loaded()
    assert gateway_two.load_markets_calls == 0


def test_from_credentials_builds_spot_only_client(monkeypatch) -> None:
    import types

    created: dict[str, object] = {}

    def fake_binance(config: dict[str, object]):
        created.update(config)

        class Client:
            def set_sandbox_mode(self, enabled: bool) -> None:
                self.sandbox_enabled = enabled

        return Client()

    fake_ccxt = types.ModuleType("ccxt")
    fake_ccxt.__dict__["binance"] = fake_binance
    monkeypatch.setitem(__import__("sys").modules, "ccxt", fake_ccxt)
    gateway = BinanceSpotPortfolioGateway.from_credentials(
        api_key="key",
        api_secret="secret",
        timeout_milliseconds=5_000,
        max_retries=0,
    )
    assert isinstance(gateway, BinanceSpotPortfolioGateway)
    assert created["options"] == {"defaultType": "spot"}
    assert created["timeout"] == 5_000


def test_parse_balances_supports_binance_info_balances_and_top_level_assets() -> None:
    payload = {
        "info": {
            "balances": [
                {"asset": "BTC", "free": "0.01", "locked": "0.0"},
                {"asset": "ETH", "free": "0.2", "locked": "0.0"},
                {"asset": "BNB", "free": "1.0", "locked": "0.0"},
                {"asset": "BNSOL", "free": "2.0", "locked": "0.0"},
                {"asset": "USDT", "free": "25.0", "locked": "0.0"},
            ]
        },
        "BTC": {"free": 0.01, "used": 0.0, "total": 0.01},
    }
    balances = _parse_balances(payload)
    assets = {balance.asset: balance.quantity for balance in balances}
    assert assets["BTC"] == pytest.approx(0.01)
    assert assets["ETH"] == pytest.approx(0.2)
    assert assets["BNB"] == pytest.approx(1.0)
    assert assets["BNSOL"] == pytest.approx(2.0)
    assert assets["USDT"] == pytest.approx(25.0)
