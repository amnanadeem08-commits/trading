"""Plugin version contracts."""

from __future__ import annotations

from threading import RLock

from ml_engine_plugins.exceptions import MLEnginePluginError
from models.common import PlatformModel, UTCDateTime, utc_now


class PluginVersion(PlatformModel):
    """Version record for the ML engine plugin framework."""

    version_id: str
    framework_schema: str
    configuration_hash: str = ""
    created_at: UTCDateTime


class PluginVersionRegistry:
    """Registry for plugin framework schema versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, PluginVersion] = {}
        self._latest: str | None = None

    def register(
        self,
        *,
        version_id: str,
        framework_schema: str,
        configuration_hash: str = "",
    ) -> PluginVersion:
        if not version_id.strip():
            msg = "version_id must not be empty"
            raise MLEnginePluginError(msg)
        version = PluginVersion(
            version_id=version_id,
            framework_schema=framework_schema,
            configuration_hash=configuration_hash,
            created_at=utc_now(),
        )
        with self._lock:
            self._versions[version_id] = version
            self._latest = version_id
        return version

    def get(self, version_id: str) -> PluginVersion:
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            msg = f"Plugin framework version not found: {version_id}"
            raise MLEnginePluginError(msg)
        return version

    def latest(self) -> PluginVersion | None:
        with self._lock:
            if self._latest is None:
                return None
            return self._versions.get(self._latest)

    def list_versions(self) -> tuple[PluginVersion, ...]:
        with self._lock:
            return tuple(self._versions[vid] for vid in sorted(self._versions))
