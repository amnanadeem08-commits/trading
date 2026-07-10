"""Inference dispatcher."""

from __future__ import annotations

import time

from inference_pipeline.lifecycle.inference_lifecycle import InferenceLifecycleManager
from inference_pipeline.metrics.inference_metrics import InferenceMetricsCollector, InferenceSummary
from inference_pipeline.registry.inference_registry import InferenceRegistry
from inference_pipeline.requests.inference_request import InferenceRequest
from inference_pipeline.responses.inference_metadata import InferenceMetadata
from inference_pipeline.responses.inference_response import InferenceResponse
from inference_pipeline.responses.inference_result import InferenceResult, InferenceStatus
from inference_pipeline.runtime.inference_context import InferenceContext
from inference_pipeline.runtime.model_loader import ModelLoader
from inference_pipeline.scheduler.inference_queue import QueuedInferenceRequest
from inference_pipeline.validation.validator import InferenceValidator
from models.common import utc_now


class InferenceDispatcher:
    """Dispatches inference requests through orchestration-only lifecycle."""

    def __init__(
        self,
        *,
        model_loader: ModelLoader,
        inference_registry: InferenceRegistry,
        lifecycle: InferenceLifecycleManager,
        metrics: InferenceMetricsCollector,
        validator: InferenceValidator | None = None,
    ) -> None:
        self._loader = model_loader
        self._registry = inference_registry
        self._lifecycle = lifecycle
        self._metrics = metrics
        self._validator = validator or InferenceValidator()

    def dispatch(self, queued: QueuedInferenceRequest) -> InferenceResponse:
        request = queued.request
        started = time.monotonic() * 1000.0
        queue_time_ms = max(0.0, started - queued.queued_at_ms)

        validation = self._validator.validate_request(request)
        if not validation.valid:
            return self._fail(
                request,
                message=validation.errors[0] if validation.errors else "validation failed",
                queue_time_ms=queue_time_ms,
            )

        try:
            model = self._loader.resolve_model(request.model_id)
            version = self._loader.resolve_production_version(request.model_id)
            self._loader.validate_production_stage(version)
            artifact_id = self._loader.load_artifact_reference(version)
            version_validation = self._validator.validate_production_version(version)
            self._validator.ensure_valid(version_validation)
        except Exception as error:
            return self._fail(request, message=str(error), queue_time_ms=queue_time_ms)

        context = InferenceContext(
            request_id=request.request_id,
            model=model,
            version=version,
            artifact_id=artifact_id,
            config_hash=version.config_hash,
            input_metadata=request.input_metadata,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
        )

        self._lifecycle.emit_started(
            request_id=request.request_id,
            model_id=request.model_id,
            version_id=version.version_id,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
        )
        self._metrics.record_status(InferenceStatus.RUNNING)

        completed_at = utc_now()
        duration_ms = max(0.0, time.monotonic() * 1000.0 - started)
        metadata = InferenceMetadata(
            request_id=request.request_id,
            model_id=request.model_id,
            version_id=version.version_id,
            artifact_id=artifact_id,
            config_hash=version.config_hash,
            checksum=version.checksum,
            stage=version.stage.value,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
            started_at=completed_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            queue_time_ms=queue_time_ms,
        )

        metadata_validation = self._validator.validate_metadata(metadata)
        self._validator.ensure_valid(metadata_validation)

        response = InferenceResponse(
            request_id=request.request_id,
            model_id=request.model_id,
            status=InferenceStatus.COMPLETED,
            metadata=metadata,
            message="orchestration completed",
        )

        result = InferenceResult(
            request_id=request.request_id,
            status=InferenceStatus.COMPLETED,
            metadata=metadata,
            message=response.message,
        )
        self._registry.update(result)
        self._lifecycle.emit_completed(
            request_id=request.request_id,
            model_id=request.model_id,
            version_id=version.version_id,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
        )
        self._metrics.record_status(InferenceStatus.COMPLETED)
        self._metrics.record_latency(duration_ms, queue_time_ms=queue_time_ms)
        self._metrics.record_summary(
            InferenceSummary(
                request_id=request.request_id,
                model_id=request.model_id,
                status=InferenceStatus.COMPLETED,
                latency_ms=duration_ms,
                queue_time_ms=queue_time_ms,
            )
        )
        _ = context
        return response

    def cancel(self, request: InferenceRequest) -> InferenceResult:
        result = InferenceResult(
            request_id=request.request_id,
            status=InferenceStatus.CANCELLED,
            message="cancelled",
        )
        self._registry.update(result)
        self._lifecycle.emit_cancelled(
            request_id=request.request_id,
            model_id=request.model_id,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
        )
        self._metrics.record_status(InferenceStatus.CANCELLED)
        return result

    def _fail(
        self,
        request: InferenceRequest,
        *,
        message: str,
        queue_time_ms: float,
    ) -> InferenceResponse:
        result = InferenceResult(
            request_id=request.request_id,
            status=InferenceStatus.FAILED,
            message=message,
        )
        self._registry.update(result)
        self._lifecycle.emit_failed(
            request_id=request.request_id,
            model_id=request.model_id,
            message=message,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
        )
        self._metrics.record_status(InferenceStatus.FAILED)
        self._metrics.record_latency(0.0, queue_time_ms=queue_time_ms)
        metadata = InferenceMetadata(
            request_id=request.request_id,
            model_id=request.model_id,
            version_id="",
            artifact_id="",
            config_hash="",
            checksum="",
            stage="",
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
            started_at=utc_now(),
            queue_time_ms=queue_time_ms,
        )
        return InferenceResponse(
            request_id=request.request_id,
            model_id=request.model_id,
            status=InferenceStatus.FAILED,
            metadata=metadata,
            message=message,
        )
