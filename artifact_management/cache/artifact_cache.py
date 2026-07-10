"""Artifact metadata cache."""

from __future__ import annotations

from threading import RLock

from artifact_management.cache.cache_entry import CacheEntry
from artifact_management.exceptions import ArtifactCacheError, ArtifactNotFoundError
from artifact_management.models.artifact_reference import ArtifactReference
from models.common import utc_now


class ArtifactCache:
    """Metadata-only artifact cache. No filesystem operations."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    @property
    def hits(self) -> int:
        with self._lock:
            return self._hits

    @property
    def misses(self) -> int:
        with self._lock:
            return self._misses

    def put(self, reference: ArtifactReference) -> CacheEntry:
        entry = CacheEntry(
            artifact_id=reference.artifact_id,
            reference=reference,
            cached_at=utc_now(),
        )
        with self._lock:
            self._entries[reference.artifact_id] = entry
        return entry

    def get(self, artifact_id: str) -> CacheEntry:
        with self._lock:
            entry = self._entries.get(artifact_id)
            if entry is None:
                self._misses += 1
                raise ArtifactNotFoundError(artifact_id)
            updated = entry.model_copy(update={"hit_count": entry.hit_count + 1})
            self._entries[artifact_id] = updated
            self._hits += 1
            return updated

    def contains(self, artifact_id: str) -> bool:
        with self._lock:
            return artifact_id in self._entries

    def remove(self, artifact_id: str) -> None:
        with self._lock:
            if artifact_id not in self._entries:
                msg = f"Cache entry not found: {artifact_id}"
                raise ArtifactCacheError(msg)
            del self._entries[artifact_id]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._hits = 0
            self._misses = 0
