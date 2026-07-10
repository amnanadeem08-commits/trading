"""Registry version contracts."""

from __future__ import annotations

from threading import RLock

from model_registry.exceptions import ModelRegistryError
from models.common import PlatformModel, UTCDateTime, utc_now


class RegistryVersion(PlatformModel):
    """Version record for the model registry itself."""

    version_id: str
    registry_schema: str
    configuration_hash: str = ""
    created_at: UTCDateTime


class RegistryVersionRegistry:
    """Registry for model registry schema versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, RegistryVersion] = {}
        self._latest: str | None = None

    def register(
        self,
        *,
        version_id: str,
        registry_schema: str,
        configuration_hash: str = "",
    ) -> RegistryVersion:
        if not version_id.strip():
            msg = "version_id must not be empty"
            raise ModelRegistryError(msg)
        version = RegistryVersion(
            version_id=version_id,
            registry_schema=registry_schema,
            configuration_hash=configuration_hash,
            created_at=utc_now(),
        )
        with self._lock:
            self._versions[version_id] = version
            self._latest = version_id
        return version

    def get(self, version_id: str) -> RegistryVersion:
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            msg = f"Registry version not found: {version_id}"
            raise ModelRegistryError(msg)
        return version

    def latest(self) -> RegistryVersion | None:
        with self._lock:
            if self._latest is None:
                return None
            return self._versions.get(self._latest)

    def list_versions(self) -> tuple[RegistryVersion, ...]:
        with self._lock:
            return tuple(self._versions[vid] for vid in sorted(self._versions))
