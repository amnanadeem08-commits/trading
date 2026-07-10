"""Feature store feature registry."""

from __future__ import annotations

from threading import RLock

from pydantic import Field

from feature_store.exceptions import FeatureRecordNotFoundError
from models.common import PlatformModel, UTCDateTime, utc_now

_default_registry: FeatureRegistry | None = None
_registry_lock = RLock()


class FeatureRegistryEntry(PlatformModel):
    """Registered feature definition in the feature store."""

    feature_name: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    dtype: str = Field(min_length=1, default="float")
    tags: tuple[str, ...] = Field(default_factory=tuple)
    created_at: UTCDateTime = Field(default_factory=utc_now)


class FeatureRegistry:
    """Thread-safe registry for individual feature definitions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, FeatureRegistryEntry] = {}

    def register(self, entry: FeatureRegistryEntry) -> None:
        with self._lock:
            self._entries[entry.feature_name] = entry

    def lookup(self, feature_name: str) -> FeatureRegistryEntry:
        with self._lock:
            entry = self._entries.get(feature_name)
        if entry is None:
            raise FeatureRecordNotFoundError(feature_name)
        return entry

    def exists(self, feature_name: str) -> bool:
        with self._lock:
            return feature_name in self._entries

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._entries.keys()))


def get_feature_store_registry() -> FeatureRegistry:
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = FeatureRegistry()
        return _default_registry


def reset_feature_store_registry() -> None:
    global _default_registry
    with _registry_lock:
        _default_registry = None
