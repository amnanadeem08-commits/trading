"""Market data registry."""

from __future__ import annotations

from threading import RLock

from market_data.exceptions import MarketRecordNotFoundError, MarketRegistrationError
from market_data.registry.market_catalog import MarketCatalogEntry

_default_registry: MarketDataRegistry | None = None
_registry_lock = RLock()


class MarketDataRegistry:
    """Thread-safe registry for market data catalog entries."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, MarketCatalogEntry] = {}
        self._versions: dict[str, tuple[str, ...]] = {}

    def register(self, entry: MarketCatalogEntry) -> None:
        """Register a market catalog entry."""
        dataset_id = entry.dataset_id
        if not dataset_id.strip():
            msg = "Dataset id must not be empty"
            raise MarketRegistrationError(msg)
        with self._lock:
            self._entries[dataset_id] = entry
            versions = self._versions.get(dataset_id, ())
            if entry.version not in versions:
                self._versions[dataset_id] = (*versions, entry.version)

    def unregister(self, dataset_id: str) -> None:
        with self._lock:
            if dataset_id not in self._entries:
                raise MarketRecordNotFoundError(dataset_id)
            del self._entries[dataset_id]
            self._versions.pop(dataset_id, None)

    def lookup(self, dataset_id: str) -> MarketCatalogEntry:
        """Look up a catalog entry by dataset id."""
        with self._lock:
            entry = self._entries.get(dataset_id)
        if entry is None:
            raise MarketRecordNotFoundError(dataset_id)
        return entry

    def exists(self, dataset_id: str) -> bool:
        with self._lock:
            return dataset_id in self._entries

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._entries.keys()))

    def version(self, dataset_id: str) -> str:
        entry = self.lookup(dataset_id)
        return entry.version

    def metadata(self, dataset_id: str) -> MarketCatalogEntry:
        return self.lookup(dataset_id)

    def capabilities(self, dataset_id: str) -> tuple[str, ...]:
        return self.lookup(dataset_id).capabilities

    def list_versions(self, dataset_id: str) -> tuple[str, ...]:
        with self._lock:
            versions = self._versions.get(dataset_id, ())
        if not versions:
            raise MarketRecordNotFoundError(dataset_id)
        return versions


def get_market_data_registry() -> MarketDataRegistry:
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = MarketDataRegistry()
        return _default_registry


def reset_market_data_registry() -> None:
    global _default_registry
    with _registry_lock:
        _default_registry = None
