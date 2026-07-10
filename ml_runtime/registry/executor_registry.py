"""Executor metadata registry."""

from __future__ import annotations

from threading import RLock

from models.common import PlatformModel, UTCDateTime, utc_now


class ExecutorMetadata(PlatformModel):
    """Metadata for a registered model executor."""

    executor_id: str
    name: str
    version: str
    capabilities: tuple[str, ...] = ()
    registered_at: UTCDateTime


class ExecutorRegistry:
    """Maintains executor metadata only."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._executors: dict[str, ExecutorMetadata] = {}

    def register(
        self,
        *,
        executor_id: str,
        name: str,
        version: str,
        capabilities: tuple[str, ...] = (),
    ) -> ExecutorMetadata:
        metadata = ExecutorMetadata(
            executor_id=executor_id,
            name=name,
            version=version,
            capabilities=capabilities,
            registered_at=utc_now(),
        )
        with self._lock:
            self._executors[executor_id] = metadata
        return metadata

    def lookup(self, executor_id: str) -> ExecutorMetadata | None:
        with self._lock:
            return self._executors.get(executor_id)

    def list_executors(self) -> tuple[ExecutorMetadata, ...]:
        with self._lock:
            return tuple(self._executors[eid] for eid in sorted(self._executors))

    def unregister(self, executor_id: str) -> None:
        with self._lock:
            self._executors.pop(executor_id, None)

    def clear(self) -> None:
        with self._lock:
            self._executors.clear()
