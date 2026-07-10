"""Market connector abstract interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from connectors.capabilities import ConnectorCapabilities
from connectors.exceptions import UnsupportedCapabilityError
from connectors.health import HealthCheckResult
from connectors.metadata import ConnectorMetadata
from models.market import MarketMetadata, NormalizedBar, NormalizedTicker, Symbol, SymbolFilter
from models.order import NormalizedOrder, OrderRequest
from models.position import NormalizedAccount, NormalizedPosition


class LiveSubscription(ABC):
    """Handle for an active live data subscription."""

    @property
    @abstractmethod
    def market_id(self) -> str:
        """Market identifier for the subscription."""

    @abstractmethod
    def unsubscribe(self) -> None:
        """Stop the live data subscription."""


class MarketConnector(ABC):
    """Abstract interface every market plugin must implement."""

    @property
    @abstractmethod
    def market_id(self) -> str:
        """Unique market identifier, e.g. crypto:binance."""

    @abstractmethod
    def metadata(self) -> ConnectorMetadata:
        """Return connector metadata for audit and versioning."""

    @abstractmethod
    def capabilities(self) -> ConnectorCapabilities:
        """Return immutable connector capability declaration."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the market data or execution provider."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection and release provider resources."""

    @abstractmethod
    def health_check(self) -> HealthCheckResult:
        """Return current connector health status."""

    @abstractmethod
    def fetch_symbols(self, filters: SymbolFilter | None = None) -> tuple[Symbol, ...]:
        """Return available symbols for this market."""

    @abstractmethod
    def fetch_historical_data(
        self,
        symbol_id: str,
        timeframe: str,
        limit: int,
    ) -> tuple[NormalizedBar, ...]:
        """Fetch normalized historical OHLCV bars."""

    @abstractmethod
    def fetch_live_data(self, symbol_id: str) -> NormalizedTicker:
        """Fetch a normalized live ticker snapshot."""

    @abstractmethod
    def subscribe_live(
        self,
        symbols: tuple[str, ...],
        callback: Callable[[NormalizedTicker], None],
    ) -> LiveSubscription:
        """Subscribe to live ticker updates for the given symbols."""

    @abstractmethod
    def market_metadata(self, symbol_id: str) -> MarketMetadata:
        """Return normalized market metadata for a symbol."""

    @abstractmethod
    def place_order(self, order: OrderRequest) -> NormalizedOrder:
        """Place an order. Concrete connectors enforce SIGNAL_ONLY gating."""

    @abstractmethod
    def cancel_order(self, order_id: str) -> NormalizedOrder:
        """Cancel an open order."""

    @abstractmethod
    def get_positions(self) -> tuple[NormalizedPosition, ...]:
        """Return current open positions."""

    @abstractmethod
    def get_account(self) -> NormalizedAccount:
        """Return current account snapshot."""

    def _raise_unsupported(self, capability: str) -> None:
        """Helper for connectors that do not support execution capabilities."""
        msg = f"Capability not supported: {capability}"
        raise UnsupportedCapabilityError(msg, market_id=self.market_id, capability=capability)
