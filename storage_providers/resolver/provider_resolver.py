"""Provider resolver."""

from __future__ import annotations

from storage_providers.contracts.provider_manifest import ProviderManifest
from storage_providers.contracts.provider_metadata import ProviderMetadata
from storage_providers.contracts.provider_type import ProviderType
from storage_providers.contracts.storage_provider import StorageProvider
from storage_providers.exceptions import ProviderResolutionError
from storage_providers.registry.provider_registry import ProviderRegistry

_SCHEME_TO_PROVIDER_TYPE: dict[str, ProviderType] = {
    "local": ProviderType.LOCAL,
    "file": ProviderType.FILE,
    "s3": ProviderType.S3,
    "gs": ProviderType.GCS,
    "gcs": ProviderType.GCS,
    "azure": ProviderType.AZURE,
    "http": ProviderType.HTTP,
    "https": ProviderType.HTTP,
}


class ProviderResolver:
    """Maps URIs to storage providers using metadata only."""

    def __init__(self, *, registry: ProviderRegistry) -> None:
        self._registry = registry

    def extract_scheme(self, uri: str) -> str:
        if "://" not in uri:
            msg = f"URI must include a scheme: {uri}"
            raise ProviderResolutionError(msg)
        return uri.split("://", 1)[0].strip().lower()

    def resolve_provider_type(self, uri: str) -> ProviderType:
        scheme = self.extract_scheme(uri)
        provider_type = _SCHEME_TO_PROVIDER_TYPE.get(scheme)
        if provider_type is None:
            return ProviderType.CUSTOM
        return provider_type

    def resolve(
        self,
        uri: str,
        *,
        manifest: ProviderManifest | None = None,
        metadata: ProviderMetadata | None = None,
    ) -> StorageProvider:
        provider = self._registry.resolve(uri)
        if manifest is not None and manifest.provider_id != provider.provider_id():
            msg = "manifest.provider_id does not match resolved provider"
            raise ProviderResolutionError(msg)
        if metadata is not None and metadata.provider_id != provider.provider_id():
            msg = "metadata.provider_id does not match resolved provider"
            raise ProviderResolutionError(msg)
        scheme = self.extract_scheme(uri)
        supported = {s.strip().lower() for s in provider.manifest().supported_uri_schemes}
        if supported and scheme not in supported:
            msg = f"Provider does not support URI scheme: {scheme}"
            raise ProviderResolutionError(msg)
        return provider
