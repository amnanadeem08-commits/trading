"""Inference runtime facade."""

from __future__ import annotations

from uuid import uuid4

from config.hash import compute_configuration_hash
from events.event_bus import EventBus
from inference_pipeline.lifecycle.inference_lifecycle import InferenceLifecycleManager
from inference_pipeline.metrics.inference_metrics import InferenceMetricsCollector
from inference_pipeline.registry.inference_registry import InferenceRegistry
from inference_pipeline.requests.inference_request import InferenceRequest
from inference_pipeline.responses.inference_response import InferenceResponse
from inference_pipeline.runtime.model_loader import ModelLoader
from inference_pipeline.scheduler.inference_dispatcher import InferenceDispatcher
from inference_pipeline.scheduler.inference_queue import InferenceQueue
from inference_pipeline.scheduler.inference_scheduler import InferenceScheduler
from inference_pipeline.validation.validator import InferenceValidator
from inference_pipeline.versioning.inference_version import InferenceVersionRegistry
from metrics.registry import MetricRegistry
from model_registry.integration.training_pipeline_bridge import ModelRegistryRuntime
from model_registry.models.model_version import ModelVersion
from model_registry.registry.model_registry import ModelRegistryStore


class InferenceRuntime:
    """Wires inference pipeline components for orchestration-only execution."""

    def __init__(
        self,
        *,
        model_registry: ModelRegistryStore,
        event_bus: EventBus | None = None,
        metrics: MetricRegistry | None = None,
        queue_size: int = 1000,
        production_only: bool = True,
    ) -> None:
        self.model_registry = model_registry
        self.model_loader = ModelLoader(model_registry)
        self.inference_registry = InferenceRegistry()
        self.version_registry = InferenceVersionRegistry()
        self.metrics_collector = InferenceMetricsCollector()
        self.validator = InferenceValidator(production_only=production_only)
        self._event_bus = event_bus or EventBus()
        self._metric_registry = metrics or MetricRegistry()
        self.lifecycle = InferenceLifecycleManager(
            event_bus=self._event_bus,
            metrics=self._metric_registry,
        )
        self.queue = InferenceQueue(max_size=queue_size)
        self.dispatcher = InferenceDispatcher(
            model_loader=self.model_loader,
            inference_registry=self.inference_registry,
            lifecycle=self.lifecycle,
            metrics=self.metrics_collector,
            validator=self.validator,
        )
        self.scheduler = InferenceScheduler(
            queue=self.queue,
            dispatcher=self.dispatcher,
            inference_registry=self.inference_registry,
            lifecycle=self.lifecycle,
            metrics=self.metrics_collector,
            validator=self.validator,
        )
        version = self.version_registry.register(
            version_id="inference-v1",
            pipeline_schema="1.0.0",
            configuration_hash=compute_configuration_hash(),
        )
        self.lifecycle.emit_runtime_initialized(
            pipeline_version=version.pipeline_schema,
            correlation_id=str(uuid4()),
            trace_id=str(uuid4()),
        )

    def submit(self, request: InferenceRequest) -> InferenceRequest:
        return self.scheduler.submit(request)

    def run_pending(self) -> tuple[InferenceResponse, ...]:
        return self.scheduler.run_all()

    def resolve_model(self, model_id: str) -> ModelVersion:
        version = self.model_loader.resolve_production_version(model_id)
        artifact_id = self.model_loader.load_artifact_reference(version)
        self.lifecycle.emit_model_resolved(
            model_id=model_id,
            version_id=version.version_id,
            artifact_id=artifact_id,
            correlation_id=str(uuid4()),
            trace_id=str(uuid4()),
        )
        return version


def build_inference_runtime(
    model_registry_runtime: ModelRegistryRuntime,
    *,
    queue_size: int = 1000,
) -> InferenceRuntime:
    """Create an inference runtime bound to a model registry."""
    return InferenceRuntime(
        model_registry=model_registry_runtime.registry,
        queue_size=queue_size,
    )


def run_inference_for_model(
    runtime: InferenceRuntime,
    *,
    model_id: str,
    input_metadata: dict[str, object],
) -> InferenceResponse:
    """Schedule and execute inference orchestration for a production model."""
    request = InferenceRequest(
        request_id=f"inference-{uuid4()}",
        model_id=model_id,
        input_metadata=input_metadata,
        correlation_id=str(uuid4()),
        trace_id=str(uuid4()),
    )
    runtime.submit(request)
    responses = runtime.run_pending()
    if not responses:
        from inference_pipeline.exceptions import InferenceDispatchError

        msg = "Inference request was not executed"
        raise InferenceDispatchError(msg)
    return responses[-1]
