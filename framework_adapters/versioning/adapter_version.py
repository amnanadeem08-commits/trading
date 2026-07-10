"""Adapter version contracts."""

from __future__ import annotations

from threading import RLock

from framework_adapters.exceptions import FrameworkAdapterError
from models.common import PlatformModel, UTCDateTime, utc_now


class AdapterVersion(PlatformModel):
    """Version record for the framework adapter layer."""

    version_id: str
    framework_schema: str
    adapter_id: str = ""
    configuration_hash: str = ""
    created_at: UTCDateTime


class AdapterVersionRegistry:
    """Registry for framework adapter schema versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, AdapterVersion] = {}
        self._latest: str | None = None

    def register(
        self,
        *,
        version_id: str,
        framework_schema: str,
        adapter_id: str = "",
        configuration_hash: str = "",
    ) -> AdapterVersion:
        if not version_id.strip():
            msg = "version_id must not be empty"
            raise FrameworkAdapterError(msg)
        version = AdapterVersion(
            version_id=version_id,
            framework_schema=framework_schema,
            adapter_id=adapter_id,
            configuration_hash=configuration_hash,
            created_at=utc_now(),
        )
        with self._lock:
            self._versions[version_id] = version
            self._latest = version_id
        return version

    def get(self, version_id: str) -> AdapterVersion:
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            msg = f"Framework adapter version not found: {version_id}"
            raise FrameworkAdapterError(msg)
        return version

    def latest(self) -> AdapterVersion | None:
        with self._lock:
            if self._latest is None:
                return None
            return self._versions.get(self._latest)

    def list_versions(self) -> tuple[AdapterVersion, ...]:
        with self._lock:
            return tuple(self._versions[vid] for vid in sorted(self._versions))
