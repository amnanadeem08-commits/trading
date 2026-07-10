"""Storage provider validator."""

from __future__ import annotations

from storage_providers.contracts.provider_manifest import ProviderManifest
from storage_providers.contracts.provider_metadata import ProviderMetadata
from storage_providers.contracts.storage_provider import StorageProvider
from storage_providers.exceptions import (
    ProviderFilesystemError,
    ProviderHealthError,
    ProviderNotFoundError,
    ProviderPathError,
    ProviderValidationError,
)
from storage_providers.health.health_result import HealthStatus
from storage_providers.health.provider_health import ProviderHealthChecker
from storage_providers.registry.provider_registry import ProviderRegistry
from storage_providers.validation.validation_result import ProviderValidationResult


class StorageProviderValidator:
    """Validates storage provider contracts without network access."""

    def __init__(self, *, registry: ProviderRegistry | None = None) -> None:
        self._registry = registry

    def validate_metadata(self, metadata: ProviderMetadata) -> ProviderValidationResult:
        errors: list[str] = []
        if not metadata.provider_id.strip():
            errors.append("provider_id must not be empty")
        if not metadata.name.strip():
            errors.append("name must not be empty")
        if not metadata.version.strip():
            errors.append("version must not be empty")
        if errors:
            return ProviderValidationResult.failure(
                *errors, provider_id=metadata.provider_id or None
            )
        return ProviderValidationResult.success(provider_id=metadata.provider_id)

    def validate_manifest(self, manifest: ProviderManifest) -> ProviderValidationResult:
        errors: list[str] = []
        if not manifest.provider_id.strip():
            errors.append("provider_id must not be empty")
        if not manifest.name.strip():
            errors.append("name must not be empty")
        if not manifest.version.strip():
            errors.append("version must not be empty")
        if not manifest.supported_uri_schemes:
            errors.append("manifest must declare supported_uri_schemes")
        if errors:
            return ProviderValidationResult.failure(
                *errors, provider_id=manifest.provider_id or None
            )
        return ProviderValidationResult.success(provider_id=manifest.provider_id)

    def validate_capabilities(self, provider: StorageProvider) -> ProviderValidationResult:
        if not provider.capabilities():
            return ProviderValidationResult.failure(
                "provider must declare at least one capability",
                provider_id=provider.provider_id(),
            )
        return ProviderValidationResult.success(provider_id=provider.provider_id())

    def validate_uri_scheme(self, uri: str, provider: StorageProvider) -> ProviderValidationResult:
        if "://" not in uri:
            return ProviderValidationResult.failure(
                "uri must include a scheme",
                provider_id=provider.provider_id(),
            )
        scheme = uri.split("://", 1)[0].strip().lower()
        supported = {s.strip().lower() for s in provider.manifest().supported_uri_schemes}
        if scheme not in supported:
            return ProviderValidationResult.failure(
                f"unsupported URI scheme for provider: {scheme}",
                provider_id=provider.provider_id(),
            )
        return ProviderValidationResult.success(provider_id=provider.provider_id())

    def validate_duplicate_registration(
        self,
        provider: StorageProvider,
    ) -> ProviderValidationResult:
        if self._registry is None:
            return ProviderValidationResult.success(provider_id=provider.provider_id())
        try:
            self._registry.lookup(provider.provider_id())
        except ProviderNotFoundError:
            return ProviderValidationResult.success(provider_id=provider.provider_id())
        return ProviderValidationResult.failure(
            "provider already registered",
            provider_id=provider.provider_id(),
        )

    def validate_metadata_completeness(
        self,
        *,
        provider: StorageProvider,
        uri: str,
    ) -> ProviderValidationResult:
        metadata_payload = provider.fetch_metadata(uri=uri)
        required_fields = ("uri", "provider_id", "complete")
        missing = [field for field in required_fields if field not in metadata_payload]
        if missing:
            return ProviderValidationResult.failure(
                f"provider metadata missing fields: {', '.join(missing)}",
                provider_id=provider.provider_id(),
            )
        if metadata_payload.get("complete") is not True:
            return ProviderValidationResult.failure(
                "provider metadata is incomplete",
                provider_id=provider.provider_id(),
            )
        return ProviderValidationResult.success(provider_id=provider.provider_id())

    def validate_file_existence(
        self,
        *,
        provider: StorageProvider,
        uri: str,
    ) -> ProviderValidationResult:
        try:
            provider.resolve(uri=uri)
        except ProviderFilesystemError as error:
            message = str(error)
            if "does not exist" in message:
                return ProviderValidationResult.failure(
                    message,
                    provider_id=provider.provider_id(),
                )
            return ProviderValidationResult.failure(
                message,
                provider_id=provider.provider_id(),
            )
        except ProviderPathError as error:
            return ProviderValidationResult.failure(
                str(error),
                provider_id=provider.provider_id(),
            )
        return ProviderValidationResult.success(provider_id=provider.provider_id())

    def validate_checksum(
        self,
        *,
        provider: StorageProvider,
        uri: str,
        expected_checksum: str,
    ) -> ProviderValidationResult:
        metadata_payload = provider.fetch_metadata(uri=uri)
        actual = str(metadata_payload.get("checksum", ""))
        if not actual:
            return ProviderValidationResult.failure(
                "provider metadata does not include checksum",
                provider_id=provider.provider_id(),
            )
        if actual != expected_checksum:
            return ProviderValidationResult.failure(
                "checksum verification failed",
                provider_id=provider.provider_id(),
            )
        return ProviderValidationResult.success(provider_id=provider.provider_id())

    def validate_provider_exists(self, provider_id: str) -> ProviderValidationResult:
        if self._registry is None:
            return ProviderValidationResult.success(provider_id=provider_id)
        try:
            self._registry.lookup(provider_id)
        except ProviderNotFoundError:
            return ProviderValidationResult.failure(
                f"provider not registered: {provider_id}",
                provider_id=provider_id,
            )
        return ProviderValidationResult.success(provider_id=provider_id)

    def validate_provider_healthy(self, provider_id: str) -> ProviderValidationResult:
        if self._registry is None:
            return ProviderValidationResult.success(provider_id=provider_id)
        checker = ProviderHealthChecker(registry=self._registry)
        try:
            result = checker.check(provider_id)
        except ProviderHealthError as error:
            return ProviderValidationResult.failure(
                str(error),
                provider_id=provider_id,
            )
        if result.status == HealthStatus.UNHEALTHY:
            return ProviderValidationResult.failure(
                result.message or "provider is unhealthy",
                provider_id=provider_id,
            )
        return ProviderValidationResult.success(provider_id=provider_id)

    def validate_resolution(
        self,
        *,
        uri: str,
        provider: StorageProvider,
        expected_checksum: str | None = None,
    ) -> ProviderValidationResult:
        scheme_result = self.validate_uri_scheme(uri, provider)
        if not scheme_result.valid:
            return scheme_result
        exists_result = self.validate_provider_exists(provider.provider_id())
        if not exists_result.valid:
            return exists_result
        healthy_result = self.validate_provider_healthy(provider.provider_id())
        if not healthy_result.valid:
            return healthy_result
        provider_result = self.validate_provider(provider, check_duplicate=False)
        if not provider_result.valid:
            return provider_result
        file_result = self.validate_file_existence(provider=provider, uri=uri)
        if not file_result.valid:
            return file_result
        metadata_result = self.validate_metadata_completeness(provider=provider, uri=uri)
        if not metadata_result.valid:
            return metadata_result
        if expected_checksum:
            checksum_result = self.validate_checksum(
                provider=provider,
                uri=uri,
                expected_checksum=expected_checksum,
            )
            if not checksum_result.valid:
                return checksum_result
        return ProviderValidationResult.success(provider_id=provider.provider_id())

    def validate_provider(
        self,
        provider: StorageProvider,
        *,
        check_duplicate: bool = True,
    ) -> ProviderValidationResult:
        metadata_result = self.validate_metadata(provider.metadata())
        if not metadata_result.valid:
            return metadata_result
        manifest_result = self.validate_manifest(provider.manifest())
        if not manifest_result.valid:
            return manifest_result
        if provider.metadata().provider_id != provider.manifest().provider_id:
            return ProviderValidationResult.failure(
                "metadata.provider_id must match manifest.provider_id",
                provider_id=provider.provider_id(),
            )
        if provider.provider_type() != provider.manifest().provider_type:
            return ProviderValidationResult.failure(
                "provider_type() must match manifest.provider_type",
                provider_id=provider.provider_id(),
            )
        capabilities_result = self.validate_capabilities(provider)
        if not capabilities_result.valid:
            return capabilities_result
        if check_duplicate:
            duplicate_result = self.validate_duplicate_registration(provider)
            if not duplicate_result.valid:
                return duplicate_result
        return ProviderValidationResult.success(provider_id=provider.provider_id())

    def ensure_valid(self, result: ProviderValidationResult) -> None:
        if not result.valid:
            message = result.errors[0] if result.errors else "validation failed"
            raise ProviderValidationError(message)
