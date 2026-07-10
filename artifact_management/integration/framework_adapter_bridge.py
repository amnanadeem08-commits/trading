"""Framework adapter bridge for artifact resolution."""

from __future__ import annotations

from artifact_management.cache.artifact_cache import ArtifactCache
from artifact_management.exceptions import ArtifactResolutionError
from artifact_management.health.artifact_health import ArtifactHealthChecker
from artifact_management.lifecycle.artifact_lifecycle import ArtifactLifecycleManager
from artifact_management.metrics.artifact_metrics import ArtifactMetricsCollector
from artifact_management.metrics.artifact_summary import ArtifactSummary
from artifact_management.models.artifact_manifest import ArtifactManifest
from artifact_management.models.artifact_metadata import ArtifactMetadata
from artifact_management.models.artifact_reference import ArtifactReference
from artifact_management.registry.artifact_record import ArtifactState
from artifact_management.registry.artifact_registry import ArtifactRegistry
from artifact_management.resolver.artifact_resolver import ArtifactResolver
from artifact_management.validation.validator import ArtifactValidator
from artifact_management.versioning.artifact_version import ArtifactVersionRegistry
from config.hash import compute_configuration_hash
from events.event_bus import EventBus
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from metrics.registry import MetricRegistry
from ml_runtime.execution.model_executor import ModelExecutor


class FrameworkAdapterArtifactBridge:
    """Resolves artifacts and loads them through framework adapters."""

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        metrics: MetricRegistry | None = None,
    ) -> None:
        self._event_bus = event_bus or EventBus()
        self._metric_registry = metrics or MetricRegistry()
        self.registry = ArtifactRegistry()
        self.cache = ArtifactCache()
        self.resolver = ArtifactResolver()
        self.validator = ArtifactValidator(registry=self.registry)
        self.lifecycle = ArtifactLifecycleManager(
            event_bus=self._event_bus,
            metrics=self._metric_registry,
        )
        self.health_checker = ArtifactHealthChecker(registry=self.registry)
        self.metrics_collector = ArtifactMetricsCollector()
        self.version_registry = ArtifactVersionRegistry()
        self.version_registry.register(
            version_id="artifact-management-v1",
            framework_schema="1.0.0",
            configuration_hash=compute_configuration_hash(),
        )

    def resolve_reference(
        self,
        *,
        reference: ArtifactReference,
        metadata: ArtifactMetadata,
        manifest: ArtifactManifest,
    ) -> ArtifactReference:
        """Accept a storage-provider-resolved artifact reference."""
        if reference.location is None:
            msg = (
                "artifact URI must be resolved through storage provider bridge "
                "before artifact reference resolution"
            )
            raise ArtifactResolutionError(msg)
        resolved = self.resolver.resolve(
            reference=reference,
            metadata=metadata,
            manifest=manifest,
        )
        self.lifecycle.emit_artifact_resolved(
            artifact_id=resolved.artifact_id,
            uri=resolved.uri,
            correlation_id=resolved.artifact_id,
            trace_id=resolved.artifact_id,
        )
        self.metrics_collector.record_resolution()
        return resolved

    def load_through_adapter(
        self,
        adapter: FrameworkAdapter,
        *,
        reference: ArtifactReference,
        metadata: ArtifactMetadata,
        manifest: ArtifactManifest,
    ) -> ModelExecutor:
        """Resolve, validate, cache, and load artifact through a framework adapter."""
        artifact_id = reference.artifact_id
        validation = self.validator.validate_reference(
            reference=reference,
            metadata=metadata,
            manifest=manifest,
        )
        if not validation.valid:
            self.lifecycle.emit_artifact_failed(
                artifact_id=artifact_id,
                message=validation.errors[0] if validation.errors else "validation failed",
                correlation_id=artifact_id,
                trace_id=artifact_id,
            )
            self.metrics_collector.record_failure()
            self.metrics_collector.record_state(ArtifactState.FAILED)
            self.validator.ensure_valid(validation)

        self.lifecycle.emit_artifact_validated(
            artifact_id=artifact_id,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )
        self.metrics_collector.record_validation()
        self.metrics_collector.record_state(ArtifactState.VALIDATED)

        resolved = self.resolve_reference(
            reference=reference,
            metadata=metadata,
            manifest=manifest,
        )

        record = self.registry.register(
            metadata=metadata,
            manifest=manifest,
            reference=resolved,
        )
        self.registry.update_state(resolved.artifact_id, ArtifactState.RESOLVED)
        self.metrics_collector.record_state(ArtifactState.RESOLVED)
        self.lifecycle.emit_artifact_registered(
            artifact_id=record.artifact_id,
            name=record.metadata.name,
            version=record.metadata.version,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )
        self.metrics_collector.record_registration()
        self.metrics_collector.record_state(ArtifactState.REGISTERED)
        self.metrics_collector.record_summary(
            ArtifactSummary(
                artifact_id=record.artifact_id,
                name=record.metadata.name,
                version=record.metadata.version,
                state=ArtifactState.REGISTERED,
                uri=resolved.uri,
            )
        )

        self.cache.put(resolved)
        self.registry.update_state(artifact_id, ArtifactState.CACHED)
        self.metrics_collector.record_state(ArtifactState.CACHED)
        self.lifecycle.emit_artifact_cached(
            artifact_id=artifact_id,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )

        self.version_registry.register(
            version_id=f"{artifact_id}-{metadata.version}",
            framework_schema=metadata.version,
            artifact_id=artifact_id,
        )

        load_result = adapter.load_artifact(
            artifact_reference=resolved.uri,
            metadata={
                "artifact_id": artifact_id,
                "checksum": resolved.checksum.value,
                "format": resolved.format,
                "version": resolved.version,
                "location": resolved.location.model_dump() if resolved.location else {},
            },
        )
        _ = load_result
        return adapter.create_executor()

    def expire_cached(self, artifact_id: str) -> None:
        """Mark a cached artifact as expired."""
        self.cache.remove(artifact_id)
        self.registry.update_state(artifact_id, ArtifactState.EXPIRED)
        self.lifecycle.emit_artifact_expired(
            artifact_id=artifact_id,
            correlation_id=artifact_id,
            trace_id=artifact_id,
        )
        self.metrics_collector.record_state(ArtifactState.EXPIRED)


def build_artifact_bridge() -> FrameworkAdapterArtifactBridge:
    """Create an artifact management bridge."""
    return FrameworkAdapterArtifactBridge()
