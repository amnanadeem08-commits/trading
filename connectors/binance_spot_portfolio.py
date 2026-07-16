"""Read-only Binance Spot portfolio gateway.

This module intentionally exposes no order placement or cancellation methods.
"""

from __future__ import annotations

import importlib
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

_T = TypeVar("_T")

_MARKET_CACHE_TTL_SECONDS = 300.0
_MARKET_CACHE: dict[int, tuple[float, Mapping[str, Mapping[str, Any]]]] = {}


class PortfolioGatewayError(RuntimeError):
    """Base read-only portfolio gateway failure."""


class PortfolioAuthenticationError(PortfolioGatewayError):
    """Binance rejected read-only account credentials."""


class PortfolioTimeoutError(PortfolioGatewayError):
    """Binance did not respond within the configured timeout."""


@dataclass(frozen=True, slots=True)
class SpotBalance:
    """Read-only Spot balance returned by the connector boundary."""

    asset: str
    free: float
    locked: float

    @property
    def quantity(self) -> float:
        return self.free + self.locked


@dataclass(frozen=True, slots=True)
class MarketEligibility:
    """Spot market validation result."""

    symbol: str
    eligible: bool
    reason: str | None = None


class BinanceExchange(Protocol):
    """Small injected ccxt surface required by portfolio synchronization."""

    def fetch_balance(self) -> Mapping[str, Any]: ...

    def load_markets(self) -> Mapping[str, Mapping[str, Any]]: ...

    def fetch_ticker(self, symbol: str) -> Mapping[str, Any]: ...

    def fetch_tickers(self, symbols: list[str] | None = None) -> Mapping[str, Mapping[str, Any]]: ...


class BinanceSpotPortfolioGateway:
    """Fetch balances, market eligibility, and prices without trading methods."""

    def __init__(self, exchange: BinanceExchange, *, max_retries: int = 1) -> None:
        self._exchange = exchange
        self._max_retries = max_retries
        self._markets: Mapping[str, Mapping[str, Any]] | None = None
        self.fetch_balance_calls = 0
        self.load_markets_calls = 0
        self.fetch_ticker_calls = 0
        self.fetch_tickers_calls = 0

    @classmethod
    def from_credentials(
        cls,
        *,
        api_key: str,
        api_secret: str,
        timeout_milliseconds: int,
        max_retries: int,
    ) -> BinanceSpotPortfolioGateway:
        """Construct an authenticated ccxt Binance client with Spot-only defaults."""
        if not api_key.strip() or not api_secret.strip():
            raise PortfolioAuthenticationError("Binance API credentials are missing")
        ccxt = importlib.import_module("ccxt")
        exchange_type = ccxt.__dict__["binance"]
        exchange = exchange_type(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "timeout": timeout_milliseconds,
                "options": {"defaultType": "spot"},
            }
        )
        if hasattr(exchange, "set_sandbox_mode"):
            exchange.set_sandbox_mode(False)
        return cls(exchange, max_retries=max_retries)

    def fetch_balances(self) -> tuple[SpotBalance, ...]:
        """Return every non-zero free/locked Spot asset balance."""
        self.fetch_balance_calls += 1
        payload = self._call(self._exchange.fetch_balance)
        return _parse_balances(payload)

    def ensure_markets_loaded(self) -> Mapping[str, Mapping[str, Any]]:
        """Load Binance market metadata once per gateway instance."""
        if self._markets is not None:
            return self._markets
        cache_key = id(self._exchange)
        cached = _MARKET_CACHE.get(cache_key)
        if cached is not None:
            cached_at, markets = cached
            if time.monotonic() - cached_at <= _MARKET_CACHE_TTL_SECONDS:
                self._markets = markets
                return markets
        self.load_markets_calls += 1
        self._markets = self._call(self._exchange.load_markets)
        _MARKET_CACHE[cache_key] = (time.monotonic(), self._markets)
        return self._markets

    def validate_spot_market(self, symbol: str) -> MarketEligibility:
        """Require existing, active, Spot-enabled, TRADING Binance market metadata."""
        markets = self.ensure_markets_loaded()
        market = markets.get(symbol)
        if market is None:
            return MarketEligibility(symbol=symbol, eligible=False, reason="missing_pair")
        info = market.get("info")
        raw_info = info if isinstance(info, Mapping) else {}
        if market.get("spot") is not True:
            return MarketEligibility(symbol=symbol, eligible=False, reason="not_spot")
        if raw_info.get("isSpotTradingAllowed") is False:
            return MarketEligibility(symbol=symbol, eligible=False, reason="restricted_asset")
        if market.get("active") is not True:
            return MarketEligibility(symbol=symbol, eligible=False, reason="inactive")
        if str(raw_info.get("status", "")).upper() != "TRADING":
            return MarketEligibility(symbol=symbol, eligible=False, reason="not_trading")
        return MarketEligibility(symbol=symbol, eligible=True)

    def fetch_current_price(self, symbol: str) -> float:
        """Return a positive current ticker price."""
        prices = self.fetch_prices((symbol,))
        try:
            return prices[symbol]
        except KeyError as error:
            raise PortfolioGatewayError(f"Price unavailable for {symbol}") from error

    def fetch_prices(self, symbols: tuple[str, ...]) -> dict[str, float]:
        """Return current prices for one or more symbols with minimal API calls."""
        if not symbols:
            return {}
        unique_symbols = tuple(dict.fromkeys(symbols))
        if len(unique_symbols) == 1:
            self.fetch_ticker_calls += 1
            ticker = self._call(lambda: self._exchange.fetch_ticker(unique_symbols[0]))
            return {unique_symbols[0]: _extract_price(unique_symbols[0], ticker)}
        self.fetch_tickers_calls += 1
        try:
            tickers = self._call(lambda: self._exchange.fetch_tickers(list(unique_symbols)))
        except Exception as error:
            translated = _translate_error(error)
            if not isinstance(translated, PortfolioGatewayError):
                raise translated from error
            return self._fetch_prices_individually(unique_symbols)
        prices: dict[str, float] = {}
        for symbol in unique_symbols:
            ticker = tickers.get(symbol)
            if not isinstance(ticker, Mapping):
                continue
            try:
                prices[symbol] = _extract_price(symbol, ticker)
            except PortfolioGatewayError:
                continue
        missing = [symbol for symbol in unique_symbols if symbol not in prices]
        if missing:
            prices.update(self._fetch_prices_individually(tuple(missing)))
        return prices

    def _fetch_prices_individually(self, symbols: tuple[str, ...]) -> dict[str, float]:
        prices: dict[str, float] = {}
        for symbol in symbols:
            self.fetch_ticker_calls += 1
            try:
                ticker = self._call(lambda symbol=symbol: self._exchange.fetch_ticker(symbol))
                prices[symbol] = _extract_price(symbol, ticker)
            except PortfolioGatewayError:
                continue
        return prices

    def _call(self, operation: Callable[[], _T]) -> _T:
        for attempt in range(self._max_retries + 1):
            try:
                return operation()
            except Exception as error:
                translated = _translate_error(error)
                if isinstance(translated, PortfolioTimeoutError) and attempt < self._max_retries:
                    continue
                raise translated from error
        raise PortfolioGatewayError("Binance operation failed")


def _parse_balances(payload: Mapping[str, Any]) -> tuple[SpotBalance, ...]:
    """Normalize ccxt and Binance-native balance payloads into Spot balances."""
    merged: dict[str, tuple[float, float, float | None]] = {}

    def merge_asset(
        asset: str,
        free: float,
        locked: float,
        total: float | None = None,
    ) -> None:
        normalized = asset.upper()
        if not normalized:
            return
        existing = merged.get(normalized, (0.0, 0.0, None))
        merged[normalized] = (
            max(existing[0], free),
            max(existing[1], locked),
            total if total is not None else existing[2],
        )

    free_values = _number_mapping(payload.get("free"))
    locked_values = _number_mapping(payload.get("used"))
    total_values = _number_mapping(payload.get("total"))
    reserved_keys = {
        "free",
        "used",
        "total",
        "info",
        "timestamp",
        "datetime",
        "raw",
        "symbol",
        "id",
        "type",
        "code",
        "msg",
    }
    for key, value in payload.items():
        if key in reserved_keys or not isinstance(value, Mapping):
            continue
        asset = str(key).upper()
        free = _to_float(value.get("free"))
        locked = _to_float(value.get("used", value.get("locked")))
        total = _to_float(value.get("total"))
        merge_asset(asset, free, locked, total if total > 0.0 else None)

    info = payload.get("info")
    if isinstance(info, Mapping):
        balances = info.get("balances")
        if isinstance(balances, list):
            for entry in balances:
                if not isinstance(entry, Mapping):
                    continue
                asset = str(entry.get("asset", "")).upper()
                free = _to_float(entry.get("free"))
                locked = _to_float(entry.get("locked", entry.get("used")))
                merge_asset(asset, free, locked, free + locked)

    assets = set(free_values) | set(locked_values) | set(total_values) | set(merged)
    balances: list[SpotBalance] = []
    for asset in sorted(assets):
        free = free_values.get(asset, merged.get(asset, (0.0, 0.0, None))[0])
        locked = locked_values.get(asset, merged.get(asset, (0.0, 0.0, None))[1])
        total = total_values.get(asset, merged.get(asset, (0.0, 0.0, None))[2])
        if total is None:
            total = free + locked
        if total <= 0.0:
            continue
        if free + locked == 0.0:
            free = total
        balances.append(
            SpotBalance(asset=asset.upper(), free=max(free, 0.0), locked=max(locked, 0.0))
        )
    return tuple(balances)


def _extract_price(symbol: str, ticker: Mapping[str, Any]) -> float:
    raw_price = ticker.get("last") or ticker.get("close")
    if raw_price is None:
        raise PortfolioGatewayError(f"Price unavailable for {symbol}")
    try:
        price = float(raw_price)
    except (TypeError, ValueError) as error:
        raise PortfolioGatewayError(f"Price unavailable for {symbol}") from error
    if price <= 0.0:
        raise PortfolioGatewayError(f"Price unavailable for {symbol}")
    return price


def _number_mapping(raw: object) -> dict[str, float]:
    if not isinstance(raw, Mapping):
        return {}
    values: dict[str, float] = {}
    for key, value in raw.items():
        try:
            values[str(key).upper()] = float(value)
        except TypeError, ValueError:
            continue
    return values


def _to_float(raw: object) -> float:
    try:
        return float(raw or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _translate_error(error: Exception) -> PortfolioGatewayError:
    name = type(error).__name__.casefold()
    message = str(error) or type(error).__name__
    if "authentication" in name or "permission" in name:
        return PortfolioAuthenticationError(message)
    if "timeout" in name or "requesttimeout" in name:
        return PortfolioTimeoutError(message)
    return PortfolioGatewayError(message)
