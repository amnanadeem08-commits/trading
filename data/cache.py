"""Dataset cache."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock
from typing import Any


class DatasetCache(ABC):
    """Abstract cache for dataset records."""

    @abstractmethod
    def get(self, key: str) -> tuple[dict[str, Any], ...] | None:
        """Retrieve cached records."""

    @abstractmethod
    def set(self, key: str, records: tuple[dict[str, Any], ...]) -> None:
        """Store records in the cache."""

    @abstractmethod
    def invalidate(self, key: str) -> None:
        """Remove cached records."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached records."""


class InMemoryDatasetCache(DatasetCache):
    """Thread-safe in-memory dataset cache."""

    def __init__(self, *, max_entries: int = 100) -> None:
        self._lock = RLock()
        self._max_entries = max_entries
        self._entries: dict[str, tuple[dict[str, Any], ...]] = {}

    def get(self, key: str) -> tuple[dict[str, Any], ...] | None:
        with self._lock:
            return self._entries.get(key)

    def set(self, key: str, records: tuple[dict[str, Any], ...]) -> None:
        with self._lock:
            if len(self._entries) >= self._max_entries and key not in self._entries:
                oldest = next(iter(self._entries))
                del self._entries[oldest]
            self._entries[key] = records

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._entries)
