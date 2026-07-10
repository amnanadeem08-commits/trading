"""Framework adapter validator."""

from __future__ import annotations

from framework_adapters.contracts.adapter_manifest import AdapterManifest
from framework_adapters.contracts.adapter_metadata import AdapterMetadata
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.exceptions import AdapterNotFoundError, AdapterValidationError
from framework_adapters.registry.adapter_registry import AdapterRegistry
from framework_adapters.validation.validation_result import FrameworkAdapterValidationResult


class FrameworkAdapterValidator:
    """Validates framework adapter contracts without environment inspection."""

    def __init__(self, *, registry: AdapterRegistry | None = None) -> None:
        self._registry = registry

    def validate_metadata(self, metadata: AdapterMetadata) -> FrameworkAdapterValidationResult:
        errors: list[str] = []
        if not metadata.adapter_id.strip():
            errors.append("adapter_id must not be empty")
        if not metadata.name.strip():
            errors.append("name must not be empty")
        if not metadata.version.strip():
            errors.append("version must not be empty")
        if errors:
            return FrameworkAdapterValidationResult.failure(
                *errors,
                adapter_id=metadata.adapter_id or None,
            )
        return FrameworkAdapterValidationResult.success(adapter_id=metadata.adapter_id)

    def validate_manifest(self, manifest: AdapterManifest) -> FrameworkAdapterValidationResult:
        errors: list[str] = []
        if not manifest.adapter_id.strip():
            errors.append("adapter_id must not be empty")
        if not manifest.name.strip():
            errors.append("name must not be empty")
        if not manifest.version.strip():
            errors.append("version must not be empty")
        if errors:
            return FrameworkAdapterValidationResult.failure(
                *errors,
                adapter_id=manifest.adapter_id or None,
            )
        return FrameworkAdapterValidationResult.success(adapter_id=manifest.adapter_id)

    def validate_capabilities(
        self,
        adapter: FrameworkAdapter,
    ) -> FrameworkAdapterValidationResult:
        if not adapter.capabilities():
            return FrameworkAdapterValidationResult.failure(
                "adapter must declare at least one capability",
                adapter_id=adapter.adapter_id(),
            )
        return FrameworkAdapterValidationResult.success(adapter_id=adapter.adapter_id())

    def validate_engine_type(
        self,
        adapter: FrameworkAdapter,
    ) -> FrameworkAdapterValidationResult:
        metadata = adapter.metadata()
        manifest = adapter.manifest()
        if metadata.engine_type != manifest.engine_type:
            return FrameworkAdapterValidationResult.failure(
                "metadata.engine_type must match manifest.engine_type",
                adapter_id=adapter.adapter_id(),
            )
        if adapter.engine_type() != metadata.engine_type:
            return FrameworkAdapterValidationResult.failure(
                "adapter.engine_type() must match metadata.engine_type",
                adapter_id=adapter.adapter_id(),
            )
        return FrameworkAdapterValidationResult.success(adapter_id=adapter.adapter_id())

    def validate_duplicate_registration(
        self,
        adapter: FrameworkAdapter,
    ) -> FrameworkAdapterValidationResult:
        if self._registry is None:
            return FrameworkAdapterValidationResult.success(adapter_id=adapter.adapter_id())
        try:
            self._registry.lookup(adapter.adapter_id())
        except AdapterNotFoundError:
            return FrameworkAdapterValidationResult.success(adapter_id=adapter.adapter_id())
        return FrameworkAdapterValidationResult.failure(
            "adapter already registered",
            adapter_id=adapter.adapter_id(),
        )

    def validate_environment(
        self,
        adapter: FrameworkAdapter,
    ) -> FrameworkAdapterValidationResult:
        environment = adapter.validate_environment()
        if str(environment.get("status", "healthy")) != "healthy":
            return FrameworkAdapterValidationResult.failure(
                "environment validation failed",
                adapter_id=adapter.adapter_id(),
            )
        return FrameworkAdapterValidationResult.success(adapter_id=adapter.adapter_id())

    def validate_adapter(
        self,
        adapter: FrameworkAdapter,
        *,
        check_duplicate: bool = True,
    ) -> FrameworkAdapterValidationResult:
        manifest_result = self.validate_manifest(adapter.manifest())
        if not manifest_result.valid:
            return manifest_result
        metadata_result = self.validate_metadata(adapter.metadata())
        if not metadata_result.valid:
            return metadata_result
        if adapter.metadata().adapter_id != adapter.adapter_id():
            return FrameworkAdapterValidationResult.failure(
                "metadata.adapter_id must match adapter.adapter_id()",
                adapter_id=adapter.adapter_id(),
            )
        if adapter.manifest().adapter_id != adapter.adapter_id():
            return FrameworkAdapterValidationResult.failure(
                "manifest.adapter_id must match adapter.adapter_id()",
                adapter_id=adapter.adapter_id(),
            )
        for result in (
            self.validate_capabilities(adapter),
            self.validate_engine_type(adapter),
            self.validate_environment(adapter),
        ):
            if not result.valid:
                return result
        if check_duplicate:
            duplicate_result = self.validate_duplicate_registration(adapter)
            if not duplicate_result.valid:
                return duplicate_result
        return FrameworkAdapterValidationResult.success(adapter_id=adapter.adapter_id())

    def ensure_valid(self, result: FrameworkAdapterValidationResult) -> None:
        if not result.valid:
            message = result.errors[0] if result.errors else "validation failed"
            raise AdapterValidationError(message)
