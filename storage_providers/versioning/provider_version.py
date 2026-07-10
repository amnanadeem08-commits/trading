"""Provider version contracts."""

from __future__ import annotations

from threading import RLock

from models.common import PlatformModel, UTCDateTime, utc_now
from storage_providers.exceptions import StorageProviderError


class ProviderVersion(PlatformModel):
    """Version record for the storage provider layer."""

    version_id: str
    provider_schema: str
    provider_id: str = ""
    configuration_hash: str = ""
    created_at: UTCDateTime


class ProviderVersionRegistry:
    """Registry for storage provider schema versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, ProviderVersion] = {}
        self._latest: str | None = None

    def register(
        self,
        *,
        version_id: str,
        provider_schema: str,
        provider_id: str = "",
        configuration_hash: str = "",
    ) -> ProviderVersion:
        if not version_id.strip():
            msg = "version_id must not be empty"
            raise StorageProviderError(msg)
        version = ProviderVersion(
            version_id=version_id,
            provider_schema=provider_schema,
            provider_id=provider_id,
            configuration_hash=configuration_hash,
            created_at=utc_now(),
        )
        with self._lock:
            self._versions[version_id] = version
            self._latest = version_id
        return version

    def get(self, version_id: str) -> ProviderVersion:
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            msg = f"Storage provider version not found: {version_id}"
            raise StorageProviderError(msg)
        return version

    def latest(self) -> ProviderVersion | None:
        with self._lock:
            if self._latest is None:
                return None
            return self._versions.get(self._latest)

    def list_versions(self) -> tuple[ProviderVersion, ...]:
        with self._lock:
            return tuple(self._versions[vid] for vid in sorted(self._versions))
