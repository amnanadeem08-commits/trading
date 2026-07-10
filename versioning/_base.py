"""Shared versioning registry primitives."""

from __future__ import annotations

from threading import RLock

from models.common import ContractViolationError, VersionInfo


class VersionRegistry:
    """In-memory version registry for a single artifact type."""

    def __init__(self, artifact_name: str) -> None:
        self._artifact_name = artifact_name
        self._lock = RLock()
        self._versions: dict[str, VersionInfo] = {}
        self._current_version_id: str | None = None

    @property
    def artifact_name(self) -> str:
        return self._artifact_name

    def register(self, version: VersionInfo, *, set_current: bool = True) -> None:
        """Register a version. Optionally mark it as current."""
        with self._lock:
            self._versions[version.version_id] = version
            if set_current:
                self._current_version_id = version.version_id

    def get(self, version_id: str) -> VersionInfo:
        """Retrieve a registered version by id."""
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            msg = f"{self._artifact_name} version not found: {version_id}"
            raise ContractViolationError(msg)
        return version

    def current(self) -> VersionInfo | None:
        """Return the current active version, if set."""
        with self._lock:
            if self._current_version_id is None:
                return None
            return self._versions.get(self._current_version_id)

    def list_versions(self) -> tuple[VersionInfo, ...]:
        """Return all registered versions sorted by version id."""
        with self._lock:
            return tuple(sorted(self._versions.values(), key=lambda item: item.version_id))

    def exists(self, version_id: str) -> bool:
        with self._lock:
            return version_id in self._versions
