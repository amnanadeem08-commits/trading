"""Helpers for storage provider tests."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from artifact_management import (
    ArtifactChecksum,
    ArtifactManifest,
    ArtifactMetadata,
    ArtifactReference,
    ChecksumAlgorithm,
    FrameworkAdapterArtifactBridge,
)
from models.common import utc_now
from storage_providers import (
    ArtifactManagementStorageBridge,
    ProviderCapability,
    ProviderManifest,
    ProviderMetadata,
    ProviderType,
    StorageProvider,
    build_storage_bridge,
    create_local_provider,
    create_stub_local_provider,
)
from tests.artifact_management_helpers import (
    STUB_ARTIFACT_ID,
    make_stub_artifact_bundle,
    make_stub_artifact_manifest,
    make_stub_artifact_metadata,
)

if TYPE_CHECKING:
    from pathlib import Path

STUB_PROVIDER_ID = "stub-provider-1"


class StubStorageProvider(StorageProvider):
    """Metadata-only storage provider for negative-path tests."""

    def __init__(
        self,
        *,
        provider_id: str = STUB_PROVIDER_ID,
        supported_schemes: tuple[str, ...] = ("local",),
        complete_metadata: bool = True,
    ) -> None:
        self._provider_id = provider_id
        self._supported_schemes = supported_schemes
        self._complete_metadata = complete_metadata

    def provider_id(self) -> str:
        return self._provider_id

    def provider_type(self) -> ProviderType:
        return ProviderType.LOCAL

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_id=self._provider_id,
            name="Stub Storage Provider",
            version="1.0.0",
            description="Stub provider for architecture validation",
            registered_at=utc_now(),
        )

    def manifest(self) -> ProviderManifest:
        return ProviderManifest(
            provider_id=self._provider_id,
            name="Stub Storage Provider",
            version="1.0.0",
            provider_type=ProviderType.LOCAL,
            supported_uri_schemes=self._supported_schemes,
            capabilities=(
                ProviderCapability.METADATA_RESOLUTION,
                ProviderCapability.CHECKSUM_SUPPORT,
            ),
            limits={"max_object_size": 0},
        )

    def capabilities(self) -> tuple[ProviderCapability, ...]:
        return self.manifest().capabilities

    def validate(self) -> dict[str, Any]:
        return {"valid": True, "provider_id": self._provider_id}

    def resolve(self, *, uri: str) -> dict[str, Any]:
        scheme = uri.split("://", 1)[0]
        return {
            "uri": uri,
            "scheme": scheme,
            "path": uri.split("://", 1)[1],
            "provider_id": self._provider_id,
            "resolved": True,
        }

    def fetch_metadata(self, *, uri: str) -> dict[str, Any]:
        if not self._complete_metadata:
            return {"uri": uri}
        return {
            "uri": uri,
            "provider_id": self._provider_id,
            "content_type": "application/octet-stream",
            "size": 0,
            "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "complete": True,
        }

    def shutdown(self) -> None:
        return None


def make_stub_storage_provider(
    *,
    provider_id: str = STUB_PROVIDER_ID,
    supported_schemes: tuple[str, ...] = ("local",),
    complete_metadata: bool = True,
) -> StubStorageProvider:
    return StubStorageProvider(
        provider_id=provider_id,
        supported_schemes=supported_schemes,
        complete_metadata=complete_metadata,
    )


def make_stub_storage_bridge(
    *,
    artifact_bridge: FrameworkAdapterArtifactBridge | None = None,
) -> ArtifactManagementStorageBridge:
    bridge = build_storage_bridge(
        artifact_bridge=artifact_bridge,
        auto_register_defaults=False,
    )
    bridge.register_provider(create_stub_local_provider())
    return bridge


def make_storage_bridge(
    *,
    artifact_bridge: FrameworkAdapterArtifactBridge | None = None,
) -> ArtifactManagementStorageBridge:
    return make_stub_storage_bridge(artifact_bridge=artifact_bridge)


def make_local_storage_bridge(artifact_root: Path) -> ArtifactManagementStorageBridge:
    bridge = build_storage_bridge(auto_register_defaults=False)
    provider = create_local_provider(artifact_root=artifact_root)
    bridge.register_provider(provider)
    bridge.provider_lifecycle.emit_provider_startup(
        provider_id=provider.provider_id(),
        correlation_id=provider.provider_id(),
        trace_id=provider.provider_id(),
        artifact_root=str(artifact_root),
    )
    return bridge


def write_test_artifact(
    artifact_root: Path,
    *,
    relative_path: str = "artifacts/stub-model/1.0.0/model.stub",
    content: bytes = b"stub model content",
) -> tuple[Path, str]:
    target = artifact_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    checksum = hashlib.sha256(content).hexdigest()
    return target, checksum


def make_local_artifact_bundle(
    artifact_root: Path,
    *,
    artifact_id: str = STUB_ARTIFACT_ID,
    relative_path: str = "artifacts/stub-model/1.0.0/model.stub",
    content: bytes = b"stub model content",
) -> tuple[ArtifactReference, ArtifactMetadata, ArtifactManifest, str]:
    _, checksum = write_test_artifact(
        artifact_root,
        relative_path=relative_path,
        content=content,
    )
    uri = f"local://{relative_path}"
    reference = ArtifactReference(
        artifact_id=artifact_id,
        uri=uri,
        checksum=ArtifactChecksum(algorithm=ChecksumAlgorithm.SHA256, value=checksum),
        version="1.0.0",
        format="stub",
        size=len(content),
        created_at=utc_now(),
    )
    return (
        reference,
        make_stub_artifact_metadata(artifact_id=artifact_id),
        make_stub_artifact_manifest(artifact_id=artifact_id),
        checksum,
    )


def make_storage_bridge_with_artifact_bundle() -> tuple[
    ArtifactManagementStorageBridge,
    ArtifactReference,
    ArtifactMetadata,
    ArtifactManifest,
]:
    bridge = make_storage_bridge()
    bundle = make_stub_artifact_bundle()
    return bridge, *bundle
