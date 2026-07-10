"""Connector plugin registry."""

from __future__ import annotations

from threading import RLock
from typing import TypeVar

from connectors.base import MarketConnector
from connectors.exceptions import ConnectorNotFoundError

ConnectorType = TypeVar("ConnectorType", bound=MarketConnector)


class ConnectorRegistry:
    """Thread-safe registry for market connector plugins."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._connector_types: dict[str, type[MarketConnector]] = {}
        self._connector_instances: dict[str, MarketConnector] = {}

    def register(self, market_id: str, connector_type: type[ConnectorType]) -> None:
        """Register a connector class for a market identifier."""
        if not market_id.strip():
            msg = "market_id must not be empty"
            raise ValueError(msg)
        with self._lock:
            self._connector_types[market_id] = connector_type
            self._connector_instances.pop(market_id, None)

    def unregister(self, market_id: str) -> None:
        """Remove a connector registration."""
        with self._lock:
            instance = self._connector_instances.pop(market_id, None)
            self._connector_types.pop(market_id, None)
        if instance is not None:
            instance.disconnect()

    def get(self, market_id: str) -> MarketConnector:
        """Resolve a connector instance by market identifier."""
        with self._lock:
            if market_id in self._connector_instances:
                return self._connector_instances[market_id]
            connector_type = self._connector_types.get(market_id)
            if connector_type is None:
                msg = f"Connector not registered for market_id: {market_id}"
                raise ConnectorNotFoundError(msg, market_id=market_id)
            instance = connector_type()
            self._connector_instances[market_id] = instance
            return instance

    def list_connectors(self) -> tuple[str, ...]:
        """Return all registered market identifiers."""
        with self._lock:
            return tuple(sorted(self._connector_types.keys()))

    def connector_exists(self, market_id: str) -> bool:
        """Return whether a connector is registered for the market identifier."""
        with self._lock:
            return market_id in self._connector_types


_default_registry: ConnectorRegistry | None = None
_registry_lock = RLock()


def get_connector_registry() -> ConnectorRegistry:
    """Return the process-wide default connector registry."""
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = ConnectorRegistry()
        return _default_registry


def reset_connector_registry() -> None:
    """Reset the default registry. Intended for tests."""
    global _default_registry
    with _registry_lock:
        if _default_registry is not None:
            for market_id in _default_registry.list_connectors():
                _default_registry.unregister(market_id)
        _default_registry = None
