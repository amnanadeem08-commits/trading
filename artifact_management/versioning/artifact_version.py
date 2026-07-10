"""Artifact version contracts."""

from __future__ import annotations

from threading import RLock

from artifact_management.exceptions import ArtifactManagementError
from models.common import PlatformModel, UTCDateTime, utc_now


class ArtifactVersion(PlatformModel):
    """Version record for the artifact management layer."""

    version_id: str
    framework_schema: str
    artifact_id: str = ""
    configuration_hash: str = ""
    created_at: UTCDateTime


class ArtifactVersionRegistry:
    """Registry for artifact management schema versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, ArtifactVersion] = {}
        self._latest: str | None = None

    def register(
        self,
        *,
        version_id: str,
        framework_schema: str,
        artifact_id: str = "",
        configuration_hash: str = "",
    ) -> ArtifactVersion:
        if not version_id.strip():
            msg = "version_id must not be empty"
            raise ArtifactManagementError(msg)
        version = ArtifactVersion(
            version_id=version_id,
            framework_schema=framework_schema,
            artifact_id=artifact_id,
            configuration_hash=configuration_hash,
            created_at=utc_now(),
        )
        with self._lock:
            self._versions[version_id] = version
            self._latest = version_id
        return version

    def get(self, version_id: str) -> ArtifactVersion:
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            msg = f"Artifact version not found: {version_id}"
            raise ArtifactManagementError(msg)
        return version

    def latest(self) -> ArtifactVersion | None:
        with self._lock:
            if self._latest is None:
                return None
            return self._versions.get(self._latest)

    def list_versions(self) -> tuple[ArtifactVersion, ...]:
        with self._lock:
            return tuple(self._versions[vid] for vid in sorted(self._versions))
