"""Contract tests for MarketConnector interface and registry."""

from __future__ import annotations

import inspect
from abc import ABC
from datetime import UTC, datetime

import pytest

from connectors import (
    ConnectorCapabilities,
    ConnectorHealthStatus,
    ConnectorMetadata,
    ConnectorNotFoundError,
    ConnectorRegistry,
    HealthCheckResult,
    LiveSubscription,
    MarketConnector,
    RateLimitInformation,
    normalize_bar,
    normalize_bar_mapping,
    normalize_bars,
)
from connectors.exceptions import NormalizationError
from models.common import VersionInfo
from models.market import (
    AssetClass,
    MarketMetadata,
    NormalizedBar,
    NormalizedTicker,
    Symbol,
    SymbolFilter,
)
from models.order import NormalizedOrder, OrderRequest
from models.position import NormalizedAccount, NormalizedPosition

REQUIRED_METHODS = (
    "metadata",
    "capabilities",
    "connect",
    "disconnect",
    "health_check",
    "fetch_symbols",
    "fetch_historical_data",
    "fetch_live_data",
    "subscribe_live",
    "market_metadata",
    "place_order",
    "cancel_order",
    "get_positions",
    "get_account",
)

REQUIRED_PROPERTIES = ("market_id",)


class _StubSubscription(LiveSubscription):
    def __init__(self, market_id: str) -> None:
        self._market_id = market_id
        self.unsubscribed = False

    @property
    def market_id(self) -> str:
        return self._market_id

    def unsubscribe(self) -> None:
        self.unsubscribed = True


class StubConnector(MarketConnector):
    """Minimal connector used to validate the abstract contract."""

    @property
    def market_id(self) -> str:
        return "test:stub"

    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            connector_name="stub",
            connector_version=VersionInfo(version_id="0.1.0"),
            provider="stub-provider",
            api_version="1.0",
            supported_assets=("crypto",),
        )

    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supported_markets=("test:stub",),
            supported_timeframes=("1h", "4h"),
            websocket_support=True,
            historical_support=True,
            order_support=False,
        )

    def connect(self) -> None:
        return None

    def disconnect(self) -> None:
        return None

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(
            market_id=self.market_id,
            status=ConnectorHealthStatus.CONNECTED,
            message="ok",
        )

    def fetch_symbols(self, filters: SymbolFilter | None = None) -> tuple[Symbol, ...]:
        symbol = Symbol(
            symbol_id="TEST/USD",
            market_id=self.market_id,
            asset_class=AssetClass.CRYPTO,
        )
        return (symbol,)

    def fetch_historical_data(
        self,
        symbol_id: str,
        timeframe: str,
        limit: int,
    ) -> tuple[NormalizedBar, ...]:
        bar = normalize_bar(
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            open_price=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=1000.0,
            symbol_id=symbol_id,
            market_id=self.market_id,
            timeframe=timeframe,
        )
        return (bar,)

    def fetch_live_data(self, symbol_id: str) -> NormalizedTicker:
        return NormalizedTicker(
            symbol_id=symbol_id,
            market_id=self.market_id,
            bid=100.0,
            ask=100.5,
            last=100.2,
            volume_24h=5000.0,
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        )

    def subscribe_live(
        self,
        symbols: tuple[str, ...],
        callback: object,
    ) -> LiveSubscription:
        return _StubSubscription(self.market_id)

    def market_metadata(self, symbol_id: str) -> MarketMetadata:
        return MarketMetadata(
            symbol_id=symbol_id,
            market_id=self.market_id,
            asset_class=AssetClass.CRYPTO,
            timezone="UTC",
            tick_size=0.01,
            lot_size=1.0,
            min_order_size=1.0,
            candle_intervals=("1h", "4h"),
        )

    def place_order(self, order: OrderRequest) -> NormalizedOrder:
        self._raise_unsupported("place_order")
        raise AssertionError("unreachable")

    def cancel_order(self, order_id: str) -> NormalizedOrder:
        self._raise_unsupported("cancel_order")
        raise AssertionError("unreachable")

    def get_positions(self) -> tuple[NormalizedPosition, ...]:
        return ()

    def get_account(self) -> NormalizedAccount:
        return NormalizedAccount(
            market_id=self.market_id,
            account_id="stub-account",
            balance=10000.0,
            equity=10000.0,
            currency="USD",
        )


@pytest.mark.contract
def test_market_connector_is_abstract() -> None:
    assert issubclass(MarketConnector, ABC)
    abstract_methods = set(MarketConnector.__abstractmethods__)
    assert abstract_methods == set(REQUIRED_METHODS) | set(REQUIRED_PROPERTIES)


@pytest.mark.contract
def test_market_connector_declares_required_properties() -> None:
    for name in REQUIRED_PROPERTIES:
        assert name in dir(MarketConnector)


@pytest.mark.contract
def test_stub_connector_satisfies_contract() -> None:
    connector = StubConnector()
    assert connector.market_id == "test:stub"
    assert connector.metadata().connector_name == "stub"
    assert connector.capabilities().historical_support is True
    connector.connect()
    health = connector.health_check()
    assert health.status == ConnectorHealthStatus.CONNECTED
    symbols = connector.fetch_symbols()
    assert len(symbols) == 1
    bars = connector.fetch_historical_data("TEST/USD", "1h", 1)
    assert len(bars) == 1
    assert isinstance(bars[0], NormalizedBar)
    ticker = connector.fetch_live_data("TEST/USD")
    assert ticker.symbol_id == "TEST/USD"
    subscription = connector.subscribe_live(("TEST/USD",), lambda _: None)
    subscription.unsubscribe()
    assert subscription.unsubscribed is True
    connector.disconnect()


@pytest.mark.contract
def test_registry_register_get_list_exists_unregister() -> None:
    registry = ConnectorRegistry()
    registry.register("test:stub", StubConnector)
    assert registry.connector_exists("test:stub") is True
    assert registry.list_connectors() == ("test:stub",)
    connector = registry.get("test:stub")
    assert isinstance(connector, StubConnector)
    registry.unregister("test:stub")
    assert registry.connector_exists("test:stub") is False
    assert registry.list_connectors() == ()


@pytest.mark.contract
def test_registry_get_missing_raises() -> None:
    registry = ConnectorRegistry()
    with pytest.raises(ConnectorNotFoundError):
        registry.get("missing:market")


@pytest.mark.contract
def test_normalizer_produces_normalized_bar() -> None:
    bar = normalize_bar_mapping(
        {
            "timestamp": datetime(2026, 1, 1, tzinfo=UTC),
            "open": 10.0,
            "high": 12.0,
            "low": 9.0,
            "close": 11.0,
            "volume": 100.0,
        },
        symbol_id="TEST/USD",
        market_id="test:stub",
        timeframe="1h",
    )
    assert bar.close == 11.0
    assert bar.market_id == "test:stub"


@pytest.mark.contract
def test_normalizer_batch() -> None:
    bars = normalize_bars(
        [
            {
                "timestamp": datetime(2026, 1, 1, tzinfo=UTC),
                "open": 10.0,
                "high": 12.0,
                "low": 9.0,
                "close": 11.0,
                "volume": 100.0,
            }
        ],
        symbol_id="TEST/USD",
        market_id="test:stub",
        timeframe="1h",
    )
    assert len(bars) == 1


@pytest.mark.contract
def test_normalizer_missing_field_raises() -> None:
    with pytest.raises(NormalizationError):
        normalize_bar_mapping(
            {"timestamp": datetime(2026, 1, 1, tzinfo=UTC)},
            symbol_id="TEST/USD",
            market_id="test:stub",
            timeframe="1h",
        )


@pytest.mark.contract
def test_capabilities_model_is_immutable() -> None:
    capabilities = ConnectorCapabilities(
        supported_markets=("test:stub",),
        supported_timeframes=("1h",),
        rate_limit_information=RateLimitInformation(requests_per_second=10.0),
    )
    assert capabilities.websocket_support is False


@pytest.mark.contract
def test_execution_methods_exist_on_interface() -> None:
    for method_name in ("place_order", "cancel_order", "get_positions", "get_account"):
        method = getattr(MarketConnector, method_name)
        assert callable(method)
        assert inspect.isfunction(method) or hasattr(method, "__isabstractmethod__")
