"""Artifact management bridge for storage provider resolution."""

from __future__ import annotations

from typing import Any

from artifact_management.health.artifact_health import ArtifactHealthChecker
from artifact_management.integration.framework_adapter_bridge import FrameworkAdapterArtifactBridge
from artifact_management.lifecycle.artifact_lifecycle import ArtifactLifecycleManager
from artifact_management.metrics.artifact_metrics import ArtifactMetricsCollector
from artifact_management.models.artifact_location import ArtifactLocation, ArtifactScheme
from artifact_management.models.artifact_manifest import ArtifactManifest
from artifact_management.models.artifact_metadata import ArtifactMetadata
from artifact_management.models.artifact_reference import ArtifactReference
from artifact_management.registry.artifact_registry import ArtifactRegistry
from artifact_management.resolver.artifact_resolver import ArtifactResolver
from artifact_management.validation.validator import ArtifactValidator
from artifact_management.versioning.artifact_version import ArtifactVersionRegistry
from config.hash import compute_configuration_hash
from events.event_bus import EventBus
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from metrics.registry import MetricRegistry
from ml_runtime.execution.model_executor import ModelExecutor
from storage_providers.exceptions import (
    ProviderFilesystemError,
    ProviderNotFoundError,
    ProviderPathError,
    ProviderResolutionError,
)
from storage_providers.health.provider_health import ProviderHealthChecker
from storage_providers.lifecycle.provider_lifecycle import ProviderLifecycleManager
from storage_providers.metrics.provider_metrics import ProviderMetricsCollector
from storage_providers.metrics.provider_summary import ProviderSummary
from storage_providers.providers import (
    LOCAL_PROVIDER_ID,
    STUB_LOCAL_PROVIDER_ID,
    create_local_provider_from_settings,
)
from storage_providers.registry.provider_record import ProviderState
from storage_providers.registry.provider_registry import ProviderRegistry
from storage_providers.resolver.provider_resolver import ProviderResolver
from storage_providers.validation.validator import StorageProviderValidator
from storage_providers.versioning.provider_version import ProviderVersionRegistry


def _build_location_from_resolution(uri: str, resolution: dict[str, Any]) -> ArtifactLocation:
    scheme_value = str(resolution.get("scheme", uri.split("://", 1)[0])).lower()
    scheme = ArtifactScheme(scheme_value)
    path = str(resolution.get("path", ""))
    bucket = str(resolution.get("bucket", ""))
    return ArtifactLocation(
        uri=uri,
        scheme=scheme,
        path=path,
        bucket=bucket,
        attributes={
            key: value
            for key, value in resolution.items()
            if key not in {"uri", "scheme", "path", "bucket"}
        },
    )


class ArtifactManagementStorageBridge:
    """Mandatory storage-provider path for artifact URI resolution."""

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        metrics: MetricRegistry | None = None,
        artifact_bridge: FrameworkAdapterArtifactBridge | None = None,
        auto_register_defaults: bool = True,
    ) -> None:
        self._event_bus = event_bus or EventBus()
        self._metric_registry = metrics or MetricRegistry()
        self.artifact_bridge = artifact_bridge or FrameworkAdapterArtifactBridge(
            event_bus=self._event_bus,
            metrics=self._metric_registry,
        )
        self.provider_registry = ProviderRegistry()
        self.provider_resolver = ProviderResolver(registry=self.provider_registry)
        self.provider_validator = StorageProviderValidator(registry=self.provider_registry)
        self.provider_lifecycle = ProviderLifecycleManager(
            event_bus=self._event_bus,
            metrics=self._metric_registry,
        )
        self.provider_health_checker = ProviderHealthChecker(registry=self.provider_registry)
        self.provider_metrics_collector = ProviderMetricsCollector()
        self.provider_version_registry = ProviderVersionRegistry()
        self.provider_version_registry.register(
            version_id="storage-providers-v1",
            provider_schema="1.0.0",
            configuration_hash=compute_configuration_hash(),
        )
        if auto_register_defaults:
            self.register_default_providers()

    @property
    def artifact_resolver(self) -> ArtifactResolver:
        return self.artifact_bridge.resolver

    @property
    def artifact_registry(self) -> ArtifactRegistry:
        return self.artifact_bridge.registry

    @property
    def artifact_validator(self) -> ArtifactValidator:
        return self.artifact_bridge.validator

    @property
    def artifact_lifecycle(self) -> ArtifactLifecycleManager:
        return self.artifact_bridge.lifecycle

    @property
    def artifact_health_checker(self) -> ArtifactHealthChecker:
        return self.artifact_bridge.health_checker

    @property
    def artifact_metrics_collector(self) -> ArtifactMetricsCollector:
        return self.artifact_bridge.metrics_collector

    @property
    def artifact_version_registry(self) -> ArtifactVersionRegistry:
        return self.artifact_bridge.version_registry

    def register_default_providers(self) -> None:
        """Register built-in providers from platform configuration."""
        from config.settings import AppSettings

        settings = AppSettings.from_sources().storage_providers
        if not settings.enabled:
            return
        if settings.default_provider == "local":
            provider = create_local_provider_from_settings()
            self.register_provider(provider)
            self.provider_lifecycle.emit_provider_startup(
                provider_id=provider.provider_id(),
                correlation_id=provider.provider_id(),
                trace_id=provider.provider_id(),
                artifact_root=str(provider.metadata().attributes.get("artifact_root", "")),
            )

    def resolve_through_provider(
        self,
        *,
        reference: ArtifactReference,
        metadata: ArtifactMetadata,
        manifest: ArtifactManifest,
    ) -> ArtifactReference:
        """Resolve an artifact URI via ProviderResolver and StorageProvider."""
        artifact_id = reference.artifact_id
        if self.artifact_bridge.cache.contains(artifact_id):
            self.provider_metrics_collector.record_cache_hit()
            cached = self.artifact_bridge.cache.get(artifact_id)
            return cached.reference

        self.provider_metrics_collector.record_cache_miss()
        try:
            provider = self.provider_resolver.resolve(reference.uri)
        except ProviderResolutionError as error:
            self._emit_resolution_failure(
                provider_id=artifact_id,
                artifact_id=artifact_id,
                message=str(error),
                invalid_path=True,
            )
            raise

        provider_id = provider.provider_id()
        self.provider_metrics_collector.record_provider_usage(provider_id)
        self.provider_metrics_collector.record_filesystem_lookup()

        validation = self.provider_validator.validate_resolution(
            uri=reference.uri,
            provider=provider,
            expected_checksum=reference.checksum.value,
        )
        if not validation.valid:
            message = validation.errors[0] if validation.errors else "validation failed"
            self._emit_validation_failure(
                provider_id=provider_id,
                artifact_id=artifact_id,
                message=message,
                invalid_path="path" in message.lower() or "traversal" in message.lower(),
                missing_file="does not exist" in message.lower(),
            )
            self.provider_validator.ensure_valid(validation)

        self.provider_lifecycle.emit_provider_validated(
            provider_id=provider_id,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )
        self.provider_metrics_collector.record_validation()
        self.provider_metrics_collector.record_state(ProviderState.VALIDATED)

        try:
            provider.validate()
            resolution = provider.resolve(uri=reference.uri)
            resource_metadata = provider.fetch_metadata(uri=reference.uri)
        except (ProviderFilesystemError, ProviderPathError) as error:
            message = str(error)
            self._emit_filesystem_failure(
                provider_id=provider_id,
                artifact_id=artifact_id,
                message=message,
                missing_file="does not exist" in message.lower(),
                invalid_path="path" in message.lower() or "traversal" in message.lower(),
            )
            raise

        self.provider_metrics_collector.record_checksum_operation()
        self.provider_lifecycle.emit_checksum_verified(
            provider_id=provider_id,
            uri=reference.uri,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )

        self.provider_lifecycle.emit_provider_resolved(
            provider_id=provider_id,
            uri=reference.uri,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )
        self.provider_metrics_collector.record_resolution()
        self.provider_metrics_collector.record_state(ProviderState.RESOLVED)

        location = _build_location_from_resolution(reference.uri, resolution)
        enriched = reference.model_copy(
            update={
                "location": location,
                "size": int(resource_metadata.get("size", reference.size)),
                "attributes": {
                    **reference.attributes,
                    "provider_id": provider_id,
                    "provider_type": provider.provider_type().value,
                    "provider_resolution": resolution,
                    "provider_metadata": resource_metadata,
                },
            }
        )

        resolved = self.artifact_resolver.resolve(
            reference=enriched,
            metadata=metadata,
            manifest=manifest,
        )

        record = self.provider_registry.lookup(provider_id)
        if record.state == ProviderState.REGISTERED:
            self.provider_registry.update_state(provider_id, ProviderState.RESOLVED)
        self.provider_metrics_collector.record_summary(
            ProviderSummary(
                provider_id=provider_id,
                name=record.metadata.name,
                version=record.metadata.version,
                state=ProviderState.RESOLVED,
                provider_type=provider.provider_type(),
                uri_scheme=reference.uri.split("://", 1)[0],
            )
        )
        return resolved

    def load_through_adapter(
        self,
        adapter: FrameworkAdapter,
        *,
        reference: ArtifactReference,
        metadata: ArtifactMetadata,
        manifest: ArtifactManifest,
    ) -> ModelExecutor:
        """Resolve via storage provider, then load through framework adapter."""
        enriched = self.resolve_through_provider(
            reference=reference,
            metadata=metadata,
            manifest=manifest,
        )
        return self.artifact_bridge.load_through_adapter(
            adapter,
            reference=enriched,
            metadata=metadata,
            manifest=manifest,
        )

    def register_provider(self, provider: object) -> None:
        """Register a storage provider and emit lifecycle events."""
        from storage_providers.contracts.storage_provider import StorageProvider

        if not isinstance(provider, StorageProvider):
            msg = "provider must implement StorageProvider"
            raise TypeError(msg)

        validation = self.provider_validator.validate_provider(provider)
        if not validation.valid:
            self.provider_metrics_collector.record_validation_failure()
            self.provider_validator.ensure_valid(validation)

        record = self.provider_registry.register(provider)
        self.provider_lifecycle.emit_provider_registered(
            provider_id=record.provider_id,
            name=record.metadata.name,
            version=record.metadata.version,
            correlation_id=record.provider_id,
            trace_id=record.provider_id,
        )
        self.provider_metrics_collector.record_registration()
        self.provider_metrics_collector.record_state(ProviderState.REGISTERED)
        self.provider_metrics_collector.record_summary_from_provider(
            provider,
            state=ProviderState.REGISTERED,
            uri_scheme=(
                provider.manifest().supported_uri_schemes[0]
                if provider.manifest().supported_uri_schemes
                else ""
            ),
        )
        self.provider_version_registry.register(
            version_id=f"{record.provider_id}-{record.metadata.version}",
            provider_schema=record.metadata.version,
            provider_id=record.provider_id,
        )

    def shutdown_provider(self, provider_id: str) -> None:
        """Shut down a registered provider."""
        provider = self.provider_registry.get_provider(provider_id)
        provider.shutdown()
        self.provider_registry.update_state(provider_id, ProviderState.SHUTDOWN)
        self.provider_lifecycle.emit_provider_shutdown(
            provider_id=provider_id,
            correlation_id=provider_id,
            trace_id=provider_id,
        )
        self.provider_metrics_collector.record_state(ProviderState.SHUTDOWN)

    def shutdown_default_providers(self) -> None:
        """Shut down built-in providers registered at bootstrap."""
        for provider_id in (LOCAL_PROVIDER_ID, STUB_LOCAL_PROVIDER_ID):
            try:
                self.provider_registry.lookup(provider_id)
            except ProviderNotFoundError:
                continue
            self.shutdown_provider(provider_id)

    def _emit_resolution_failure(
        self,
        *,
        provider_id: str,
        artifact_id: str,
        message: str,
        invalid_path: bool,
    ) -> None:
        self.provider_lifecycle.emit_provider_failed(
            provider_id=provider_id,
            message=message,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )
        self.provider_metrics_collector.record_resolution_failure()
        if invalid_path:
            self.provider_metrics_collector.record_invalid_path()

    def _emit_validation_failure(
        self,
        *,
        provider_id: str,
        artifact_id: str,
        message: str,
        invalid_path: bool,
        missing_file: bool,
    ) -> None:
        self.provider_lifecycle.emit_provider_failed(
            provider_id=provider_id,
            message=message,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )
        self.provider_metrics_collector.record_validation_failure()
        self.provider_metrics_collector.record_state(ProviderState.FAILED)
        if invalid_path:
            self.provider_metrics_collector.record_invalid_path()
        if missing_file:
            self.provider_metrics_collector.record_missing_file()

    def _emit_filesystem_failure(
        self,
        *,
        provider_id: str,
        artifact_id: str,
        message: str,
        missing_file: bool,
        invalid_path: bool,
    ) -> None:
        self.provider_lifecycle.emit_filesystem_failure(
            provider_id=provider_id,
            message=message,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )
        self.provider_lifecycle.emit_provider_failed(
            provider_id=provider_id,
            message=message,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )
        self.provider_metrics_collector.record_resolution_failure()
        if missing_file:
            self.provider_metrics_collector.record_missing_file()
        if invalid_path:
            self.provider_metrics_collector.record_invalid_path()


def build_storage_bridge(
    *,
    artifact_bridge: FrameworkAdapterArtifactBridge | None = None,
    auto_register_defaults: bool = True,
) -> ArtifactManagementStorageBridge:
    """Create an artifact management storage bridge."""
    return ArtifactManagementStorageBridge(
        artifact_bridge=artifact_bridge,
        auto_register_defaults=auto_register_defaults,
    )
