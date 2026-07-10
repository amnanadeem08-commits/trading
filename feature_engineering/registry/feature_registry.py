"""Feature registry."""

from __future__ import annotations

from threading import RLock

from feature_engineering.exceptions import FeatureNotFoundError, FeatureRegistrationError
from feature_engineering.registry.feature_catalog import FeatureCatalogEntry

_default_registry: FeatureRegistry | None = None
_registry_lock = RLock()


class FeatureRegistry:
    """Thread-safe registry for feature catalog entries."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, FeatureCatalogEntry] = {}
        self._versions: dict[str, tuple[str, ...]] = {}

    def register(self, entry: FeatureCatalogEntry) -> None:
        feature_id = entry.feature_id
        if not feature_id.strip():
            msg = "Feature id must not be empty"
            raise FeatureRegistrationError(msg)
        with self._lock:
            self._entries[feature_id] = entry
            versions = self._versions.get(feature_id, ())
            if entry.version not in versions:
                self._versions[feature_id] = (*versions, entry.version)

    def unregister(self, feature_id: str) -> None:
        with self._lock:
            if feature_id not in self._entries:
                raise FeatureNotFoundError(feature_id)
            del self._entries[feature_id]
            self._versions.pop(feature_id, None)

    def lookup(self, feature_id: str) -> FeatureCatalogEntry:
        with self._lock:
            entry = self._entries.get(feature_id)
        if entry is None:
            raise FeatureNotFoundError(feature_id)
        return entry

    def exists(self, feature_id: str) -> bool:
        with self._lock:
            return feature_id in self._entries

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._entries.keys()))

    def version(self, feature_id: str) -> str:
        return self.lookup(feature_id).version

    def metadata(self, feature_id: str) -> FeatureCatalogEntry:
        return self.lookup(feature_id)

    def capabilities(self, feature_id: str) -> tuple[str, ...]:
        return self.lookup(feature_id).capabilities

    def list_versions(self, feature_id: str) -> tuple[str, ...]:
        with self._lock:
            versions = self._versions.get(feature_id, ())
        if not versions:
            raise FeatureNotFoundError(feature_id)
        return versions


def get_feature_registry() -> FeatureRegistry:
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = FeatureRegistry()
        return _default_registry


def reset_feature_registry() -> None:
    global _default_registry
    with _registry_lock:
        _default_registry = None
