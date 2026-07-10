"""Concrete local filesystem storage provider."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from models.common import utc_now
from storage_providers.contracts.provider_capability import ProviderCapability
from storage_providers.contracts.provider_manifest import ProviderManifest
from storage_providers.contracts.provider_metadata import ProviderMetadata
from storage_providers.contracts.provider_type import ProviderType
from storage_providers.contracts.storage_provider import StorageProvider
from storage_providers.exceptions import ProviderFilesystemError, ProviderPathError
from storage_providers.providers.path_sandbox import PathSandbox, PathSandboxConfig

LOCAL_PROVIDER_ID = "local-provider"
_CHECKSUM_CHUNK_SIZE = 65536


@dataclass(frozen=True)
class LocalProviderConfig:
    """Runtime configuration for the local storage provider."""

    artifact_root: Path
    allow_symlinks: bool = False
    follow_links: bool = False
    compute_checksums: bool = True
    cache_metadata: bool = True


class LocalStorageProvider(StorageProvider):
    """Filesystem-backed storage provider with sandboxed metadata access."""

    def __init__(self, config: LocalProviderConfig) -> None:
        self._config = config
        self._sandbox = PathSandbox(
            PathSandboxConfig(
                artifact_root=config.artifact_root,
                allow_symlinks=config.allow_symlinks,
                follow_links=config.follow_links,
            )
        )
        self._lock = RLock()
        self._metadata_cache: dict[str, dict[str, Any]] = {}
        self._started = False

    def provider_id(self) -> str:
        return LOCAL_PROVIDER_ID

    def provider_type(self) -> ProviderType:
        return ProviderType.LOCAL

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_id=LOCAL_PROVIDER_ID,
            name="Local Storage Provider",
            version="1.0.0",
            description="Sandboxed local filesystem storage provider",
            registered_at=utc_now(),
            attributes={
                "artifact_root": str(self._config.artifact_root),
                "compute_checksums": self._config.compute_checksums,
                "cache_metadata": self._config.cache_metadata,
            },
        )

    def manifest(self) -> ProviderManifest:
        return ProviderManifest(
            provider_id=LOCAL_PROVIDER_ID,
            name="Local Storage Provider",
            version="1.0.0",
            provider_type=ProviderType.LOCAL,
            supported_uri_schemes=("local", "file"),
            capabilities=(
                ProviderCapability.METADATA_RESOLUTION,
                ProviderCapability.CHECKSUM_SUPPORT,
                ProviderCapability.VERSIONING,
                ProviderCapability.CACHING,
            ),
            limits={"max_object_size": 0},
            attributes={"sandbox_root": str(self._sandbox.artifact_root)},
        )

    def capabilities(self) -> tuple[ProviderCapability, ...]:
        return self.manifest().capabilities

    def startup(self) -> dict[str, Any]:
        with self._lock:
            self._started = True
        return {
            "provider_id": LOCAL_PROVIDER_ID,
            "artifact_root": str(self._sandbox.artifact_root),
            "started": True,
        }

    def validate(self) -> dict[str, Any]:
        root = self._sandbox.artifact_root
        if not root.exists():
            msg = f"Artifact root does not exist: {root}"
            raise ProviderFilesystemError(msg)
        if not root.is_dir():
            msg = f"Artifact root is not a directory: {root}"
            raise ProviderFilesystemError(msg)
        if not self._started:
            self.startup()
        return {
            "valid": True,
            "provider_id": LOCAL_PROVIDER_ID,
            "artifact_root": str(root),
        }

    def resolve(self, *, uri: str) -> dict[str, Any]:
        path = self._resolve_existing_path(uri)
        relative = self._sandbox.relative_path(path)
        scheme = uri.split("://", 1)[0].lower()
        return {
            "uri": uri,
            "scheme": scheme,
            "path": relative,
            "provider_id": LOCAL_PROVIDER_ID,
            "provider_type": ProviderType.LOCAL.value,
            "resolved": True,
            "location_type": "local",
            "artifact_root": str(self._sandbox.artifact_root),
        }

    def fetch_metadata(self, *, uri: str) -> dict[str, Any]:
        if self._config.cache_metadata:
            with self._lock:
                cached = self._metadata_cache.get(uri)
            if cached is not None:
                return cached

        path = self._resolve_existing_path(uri)
        stat = path.stat()
        relative = self._sandbox.relative_path(path)
        extension = path.suffix.lstrip(".")
        checksum = self._compute_checksum(path) if self._config.compute_checksums else ""
        metadata = {
            "uri": uri,
            "provider_id": LOCAL_PROVIDER_ID,
            "scheme": uri.split("://", 1)[0].lower(),
            "path": relative,
            "relative_path": relative,
            "artifact_id": relative.replace("/", "-"),
            "size": stat.st_size,
            "created_at": _timestamp_to_iso(stat.st_ctime),
            "modified_at": _timestamp_to_iso(stat.st_mtime),
            "extension": extension,
            "checksum_algorithm": "sha256",
            "checksum": checksum,
            "content_type": "application/octet-stream",
            "complete": True,
        }
        if self._config.cache_metadata:
            with self._lock:
                self._metadata_cache[uri] = metadata
        return metadata

    def verify_checksum(self, *, uri: str, expected_checksum: str) -> bool:
        metadata = self.fetch_metadata(uri=uri)
        actual = str(metadata.get("checksum", ""))
        return actual == expected_checksum

    def shutdown(self) -> None:
        with self._lock:
            self._metadata_cache.clear()
            self._started = False

    def _resolve_existing_path(self, uri: str) -> Path:
        try:
            path = self._sandbox.resolve_uri_to_path(uri)
        except ProviderPathError as error:
            msg = str(error)
            raise ProviderFilesystemError(msg) from error
        if not path.exists():
            msg = f"Artifact file does not exist: {path}"
            raise ProviderFilesystemError(msg)
        if not path.is_file():
            msg = f"Artifact path is not a file: {path}"
            raise ProviderFilesystemError(msg)
        return path

    def _compute_checksum(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(_CHECKSUM_CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()


def _timestamp_to_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def create_local_provider(
    *,
    artifact_root: str | Path,
    allow_symlinks: bool = False,
    follow_links: bool = False,
    compute_checksums: bool = True,
    cache_metadata: bool = True,
) -> LocalStorageProvider:
    """Create a configured local storage provider."""
    return LocalStorageProvider(
        LocalProviderConfig(
            artifact_root=Path(artifact_root),
            allow_symlinks=allow_symlinks,
            follow_links=follow_links,
            compute_checksums=compute_checksums,
            cache_metadata=cache_metadata,
        )
    )


def create_local_provider_from_settings() -> LocalStorageProvider:
    """Create a local provider using platform settings."""
    from config.settings import AppSettings

    settings = AppSettings.from_sources().storage_providers
    return create_local_provider(
        artifact_root=settings.artifact_root,
        allow_symlinks=settings.allow_symlinks,
        follow_links=settings.follow_links,
        compute_checksums=settings.compute_checksums,
        cache_metadata=settings.cache_metadata,
    )
