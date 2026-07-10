"""Runtime version contracts."""

from __future__ import annotations

from threading import RLock

from ml_runtime.exceptions import MLRuntimeError
from models.common import PlatformModel, UTCDateTime, utc_now


class RuntimeVersion(PlatformModel):
    """Version record for the ML runtime."""

    version_id: str
    runtime_schema: str
    configuration_hash: str = ""
    created_at: UTCDateTime


class RuntimeVersionRegistry:
    """Registry for ML runtime schema versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, RuntimeVersion] = {}
        self._latest: str | None = None

    def register(
        self,
        *,
        version_id: str,
        runtime_schema: str,
        configuration_hash: str = "",
    ) -> RuntimeVersion:
        if not version_id.strip():
            msg = "version_id must not be empty"
            raise MLRuntimeError(msg)
        version = RuntimeVersion(
            version_id=version_id,
            runtime_schema=runtime_schema,
            configuration_hash=configuration_hash,
            created_at=utc_now(),
        )
        with self._lock:
            self._versions[version_id] = version
            self._latest = version_id
        return version

    def get(self, version_id: str) -> RuntimeVersion:
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            msg = f"Runtime version not found: {version_id}"
            raise MLRuntimeError(msg)
        return version

    def latest(self) -> RuntimeVersion | None:
        with self._lock:
            if self._latest is None:
                return None
            return self._versions.get(self._latest)

    def list_versions(self) -> tuple[RuntimeVersion, ...]:
        with self._lock:
            return tuple(self._versions[vid] for vid in sorted(self._versions))
