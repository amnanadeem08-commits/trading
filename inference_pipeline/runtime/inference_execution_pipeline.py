"""Production inference execution pipeline."""

from __future__ import annotations

import time
from typing import Any

from inference_pipeline.lifecycle.inference_lifecycle import InferenceLifecycleManager
from inference_pipeline.metrics.inference_metrics import InferenceMetricsCollector
from inference_pipeline.requests.inference_request import InferenceRequest
from inference_pipeline.responses.inference_response import InferenceResponse
from inference_pipeline.responses.inference_result import InferenceStatus
from inference_pipeline.runtime.execution_router import ExecutionRouter
from inference_pipeline.runtime.inference_context import InferenceExecutionContext
from inference_pipeline.runtime.inference_request import InferenceExecutionRequest
from inference_pipeline.runtime.inference_response import InferenceExecutionResponse
from inference_pipeline.runtime.inference_runtime import InferenceRuntime
from inference_pipeline.runtime.input_binding import InputBinding
from inference_pipeline.runtime.output_normalizer import OutputNormalizer
from inference_pipeline.validation.execution_validator import InferenceExecutionValidator
from models.common import utc_now


class InferenceExecutionPipeline:
    """Transforms feature data into model execution and normalized outputs."""

    def __init__(
        self,
        *,
        inference_runtime: InferenceRuntime,
        lifecycle: InferenceLifecycleManager,
        metrics: InferenceMetricsCollector,
        router: ExecutionRouter,
        validator: InferenceExecutionValidator | None = None,
        input_binding: InputBinding | None = None,
        output_normalizer: OutputNormalizer | None = None,
    ) -> None:
        self._runtime = inference_runtime
        self._lifecycle = lifecycle
        self._metrics = metrics
        self._router = router
        self._validator = validator or InferenceExecutionValidator()
        self._input_binding = input_binding or InputBinding(validator=self._validator)
        self._output_normalizer = output_normalizer or OutputNormalizer()

    def execute(self, request: InferenceExecutionRequest) -> InferenceExecutionResponse:
        """Run the full inference execution pipeline."""
        started = time.monotonic() * 1000.0
        self._lifecycle.emit_inference_request_received(
            request_id=request.request_id,
            model_id=request.model_id,
            correlation_id=request.correlation_id or request.request_id,
            trace_id=request.trace_id or request.request_id,
        )

        validation = self._validator.validate_execution_request(
            model_id=request.model_id,
            schema=request.input_schema,
            features=request.features,
            request_id=request.request_id,
        )
        if not validation.valid:
            return self._fail(request, message=validation.errors[0], started_ms=started)

        try:
            bound_input, binding_ms = self._input_binding.bind(
                schema=request.input_schema,
                features=request.features,
            )
        except ValueError as error:
            self._metrics.record_validation_failure()
            return self._fail(request, message=str(error), started_ms=started)

        bound_validation = self._validator.validate_bound_input(
            schema=request.input_schema,
            bound_input=bound_input,
        )
        if not bound_validation.valid:
            self._metrics.record_validation_failure()
            message = bound_validation.errors[0] if bound_validation.errors else "binding failed"
            return self._fail(request, message=message, started_ms=started)

        self._metrics.record_feature_mapping(binding_ms)
        self._metrics.record_input_binding(binding_ms)
        self._lifecycle.emit_features_bound(
            request_id=request.request_id,
            model_id=request.model_id,
            correlation_id=request.correlation_id or request.request_id,
            trace_id=request.trace_id or request.request_id,
        )

        orchestration_request = InferenceRequest(
            request_id=request.request_id,
            model_id=request.model_id,
            input_metadata={
                "features": request.features,
                "bound_input": bound_input,
                "feature_version": request.feature_version,
                "schema_version": request.input_schema.schema_version,
                **bound_input,
            },
            options=request.options,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
        )
        self._runtime.submit(orchestration_request)
        responses = self._runtime.run_pending()
        if not responses:
            return self._fail(
                request, message="orchestration produced no response", started_ms=started
            )
        orchestration_response = responses[-1]
        if orchestration_response.status != InferenceStatus.COMPLETED:
            return self._fail(
                request,
                message=orchestration_response.message,
                started_ms=started,
                orchestration_response=orchestration_response,
            )

        execution_context = InferenceExecutionContext(
            request_id=request.request_id,
            model_id=request.model_id,
            artifact_id=request.artifact_id or orchestration_response.metadata.artifact_id,
            adapter_id=request.adapter_id,
            feature_version=request.feature_version,
            correlation_id=request.correlation_id or request.request_id,
            trace_id=request.trace_id or request.request_id,
        )
        enriched_response = self._attach_bound_input(orchestration_response, bound_input)

        route_input = {**bound_input, **request.execution_attributes}
        exec_started = time.monotonic() * 1000.0
        self._lifecycle.emit_model_execution_started(
            request_id=request.request_id,
            model_id=request.model_id,
            correlation_id=execution_context.correlation_id,
            trace_id=execution_context.trace_id,
        )
        try:
            outcome = self._router.route(
                enriched_response,
                execution_context=execution_context,
                bound_input=route_input,
            )
        except Exception as error:
            return self._fail(request, message=str(error), started_ms=started)
        execution_latency_ms = max(0.0, time.monotonic() * 1000.0 - exec_started)
        self._metrics.record_execution_latency(execution_latency_ms)

        if outcome.status != "completed":
            return self._fail(
                request, message=outcome.message or "execution failed", started_ms=started
            )

        self._lifecycle.emit_model_execution_completed(
            request_id=request.request_id,
            model_id=request.model_id,
            correlation_id=execution_context.correlation_id,
            trace_id=execution_context.trace_id,
        )

        raw_outputs = outcome.attributes.get("inference_outputs", [])
        if not isinstance(raw_outputs, list):
            raw_outputs = [raw_outputs]
        normalized = self._output_normalizer.normalize(
            output_type=request.input_schema.output_type,
            raw_outputs=raw_outputs,
        )
        self._metrics.record_output_normalization(normalized.duration_ms)
        self._lifecycle.emit_output_normalized(
            request_id=request.request_id,
            model_id=request.model_id,
            correlation_id=execution_context.correlation_id,
            trace_id=execution_context.trace_id,
        )

        total_latency_ms = max(0.0, time.monotonic() * 1000.0 - started)
        self._metrics.record_total_inference_latency(total_latency_ms)
        self._lifecycle.emit_inference_completed(
            request_id=request.request_id,
            model_id=request.model_id,
            correlation_id=execution_context.correlation_id,
            trace_id=execution_context.trace_id,
        )

        return InferenceExecutionResponse(
            request_id=request.request_id,
            model_id=request.model_id,
            status=InferenceStatus.COMPLETED,
            orchestration_response=enriched_response,
            normalized_output=normalized.as_dict(),
            execution_attributes=dict(outcome.attributes),
            message="inference execution completed",
            total_latency_ms=total_latency_ms,
            feature_mapping_ms=binding_ms,
            input_binding_ms=binding_ms,
            execution_latency_ms=execution_latency_ms,
            normalization_ms=normalized.duration_ms,
            completed_at=utc_now(),
        )

    @staticmethod
    def _attach_bound_input(
        response: InferenceResponse,
        bound_input: dict[str, object],
    ) -> InferenceResponse:
        metadata = response.metadata.model_copy(
            update={"attributes": {**response.metadata.attributes, **bound_input}},
        )
        return response.model_copy(update={"metadata": metadata})

    def _fail(
        self,
        request: InferenceExecutionRequest,
        *,
        message: str,
        started_ms: float,
        orchestration_response: InferenceResponse | None = None,
    ) -> InferenceExecutionResponse:
        self._lifecycle.emit_inference_failed(
            request_id=request.request_id,
            model_id=request.model_id,
            message=message,
            correlation_id=request.correlation_id or request.request_id,
            trace_id=request.trace_id or request.request_id,
        )
        self._metrics.record_validation_failure()
        total_latency_ms = max(0.0, time.monotonic() * 1000.0 - started_ms)
        self._metrics.record_total_inference_latency(total_latency_ms)
        return InferenceExecutionResponse(
            request_id=request.request_id,
            model_id=request.model_id,
            status=InferenceStatus.FAILED,
            orchestration_response=orchestration_response
            or InferenceResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=InferenceStatus.FAILED,
                metadata=self._empty_metadata(request),
                message=message,
            ),
            normalized_output={},
            message=message,
            total_latency_ms=total_latency_ms,
            completed_at=utc_now(),
        )

    @staticmethod
    def _empty_metadata(request: InferenceExecutionRequest) -> Any:
        from inference_pipeline.responses.inference_metadata import InferenceMetadata

        return InferenceMetadata(
            request_id=request.request_id,
            model_id=request.model_id,
            version_id="",
            artifact_id=request.artifact_id,
            config_hash="",
            checksum="",
            stage="",
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
            started_at=utc_now(),
        )
