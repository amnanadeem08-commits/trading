"""Built-in metadata-only local storage provider."""

from __future__ import annotations

from typing import Any

from models.common import utc_now
from storage_providers.contracts.provider_capability import ProviderCapability
from storage_providers.contracts.provider_manifest import ProviderManifest
from storage_providers.contracts.provider_metadata import ProviderMetadata
from storage_providers.contracts.provider_type import ProviderType
from storage_providers.contracts.storage_provider import StorageProvider

STUB_LOCAL_PROVIDER_ID = "stub-local-provider"
STUB_LOCAL_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
_STUB_MANIFEST_FILES: dict[str, tuple[str, ...]] = {
    "stub-model": ("model.stub", "manifest.json"),
    "artifacts": ("model.stub", "manifest.json"),
}


class StubLocalProvider(StorageProvider):
    """Metadata-only LOCAL provider with deterministic resolution."""

    def provider_id(self) -> str:
        return STUB_LOCAL_PROVIDER_ID

    def provider_type(self) -> ProviderType:
        return ProviderType.LOCAL

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_id=STUB_LOCAL_PROVIDER_ID,
            name="Stub Local Provider",
            version="1.0.0",
            description="Built-in metadata-only local storage provider",
            registered_at=utc_now(),
            attributes={"sandbox": True},
        )

    def manifest(self) -> ProviderManifest:
        return ProviderManifest(
            provider_id=STUB_LOCAL_PROVIDER_ID,
            name="Stub Local Provider",
            version="1.0.0",
            provider_type=ProviderType.LOCAL,
            supported_uri_schemes=("local",),
            capabilities=(
                ProviderCapability.METADATA_RESOLUTION,
                ProviderCapability.CHECKSUM_SUPPORT,
                ProviderCapability.VERSIONING,
                ProviderCapability.CACHING,
            ),
            limits={"max_object_size": 0},
            attributes={"deterministic": True},
        )

    def capabilities(self) -> tuple[ProviderCapability, ...]:
        return self.manifest().capabilities

    def validate(self) -> dict[str, Any]:
        return {
            "valid": True,
            "provider_id": STUB_LOCAL_PROVIDER_ID,
            "provider_type": ProviderType.LOCAL.value,
        }

    def resolve(self, *, uri: str) -> dict[str, Any]:
        scheme, remainder = uri.split("://", 1)
        return {
            "uri": uri,
            "scheme": scheme.lower(),
            "path": remainder,
            "provider_id": STUB_LOCAL_PROVIDER_ID,
            "provider_type": ProviderType.LOCAL.value,
            "resolved": True,
            "location_type": "local",
        }

    def fetch_metadata(self, *, uri: str) -> dict[str, Any]:
        scheme, remainder = uri.split("://", 1)
        manifest_key = remainder.split("/", 1)[0] if remainder else "artifacts"
        manifest_files = _STUB_MANIFEST_FILES.get(manifest_key, ("model.stub", "manifest.json"))
        return {
            "uri": uri,
            "provider_id": STUB_LOCAL_PROVIDER_ID,
            "scheme": scheme.lower(),
            "path": remainder,
            "content_type": "application/octet-stream",
            "size": 1024,
            "checksum_algorithm": "sha256",
            "checksum": STUB_LOCAL_CHECKSUM,
            "manifest_files": manifest_files,
            "version": "1.0.0",
            "complete": True,
        }

    def shutdown(self) -> None:
        return None


def create_stub_local_provider() -> StubLocalProvider:
    """Create the built-in stub local provider."""
    return StubLocalProvider()
