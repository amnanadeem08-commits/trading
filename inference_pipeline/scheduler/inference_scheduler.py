"""Inference scheduler."""

from __future__ import annotations

from uuid import uuid4

from inference_pipeline.exceptions import InferenceValidationError
from inference_pipeline.lifecycle.inference_lifecycle import InferenceLifecycleManager
from inference_pipeline.metrics.inference_metrics import InferenceMetricsCollector
from inference_pipeline.registry.inference_registry import InferenceRegistry
from inference_pipeline.requests.inference_batch_request import InferenceBatchRequest
from inference_pipeline.requests.inference_request import InferenceRequest
from inference_pipeline.responses.inference_response import InferenceResponse
from inference_pipeline.responses.inference_result import InferenceStatus
from inference_pipeline.scheduler.inference_dispatcher import InferenceDispatcher
from inference_pipeline.scheduler.inference_queue import InferenceQueue
from inference_pipeline.validation.validator import InferenceValidator


class InferenceScheduler:
    """Schedules and executes inference requests through queue and dispatcher."""

    def __init__(
        self,
        *,
        queue: InferenceQueue,
        dispatcher: InferenceDispatcher,
        inference_registry: InferenceRegistry,
        lifecycle: InferenceLifecycleManager,
        metrics: InferenceMetricsCollector,
        validator: InferenceValidator | None = None,
    ) -> None:
        self._queue = queue
        self._dispatcher = dispatcher
        self._registry = inference_registry
        self._lifecycle = lifecycle
        self._metrics = metrics
        self._validator = validator or InferenceValidator()

    def submit(self, request: InferenceRequest) -> InferenceRequest:
        validation = self._validator.validate_request(request)
        if not validation.valid:
            msg = validation.errors[0] if validation.errors else "invalid request"
            raise InferenceValidationError(msg)

        resolved = request.model_copy(
            update={
                "correlation_id": request.correlation_id or str(uuid4()),
                "trace_id": request.trace_id or str(uuid4()),
            }
        )
        self._queue.enqueue(resolved)
        self._lifecycle.emit_queued(
            request_id=resolved.request_id,
            model_id=resolved.model_id,
            correlation_id=resolved.correlation_id,
            trace_id=resolved.trace_id,
        )
        self._metrics.record_status(InferenceStatus.QUEUED)
        return resolved

    def submit_batch(self, batch: InferenceBatchRequest) -> tuple[InferenceRequest, ...]:
        validation = self._validator.validate_batch_request(batch)
        if not validation.valid:
            msg = validation.errors[0] if validation.errors else "invalid batch request"
            raise InferenceValidationError(msg)

        requests: list[InferenceRequest] = []
        for index, input_metadata in enumerate(batch.input_metadata_batch):
            request = InferenceRequest(
                request_id=f"{batch.batch_id}-{index}",
                model_id=batch.model_id,
                input_metadata=input_metadata,
                options=batch.options,
                correlation_id=batch.correlation_id or str(uuid4()),
                trace_id=batch.trace_id or str(uuid4()),
                tags=batch.tags,
            )
            requests.append(self.submit(request))
        return tuple(requests)

    def run_next(self) -> InferenceResponse | None:
        queued = self._queue.dequeue()
        if queued is None:
            return None
        response = self._dispatcher.dispatch(queued)
        self._queue.update(queued.request.request_id, status=response.status)
        return response

    def run_all(self) -> tuple[InferenceResponse, ...]:
        responses: list[InferenceResponse] = []
        while True:
            response = self.run_next()
            if response is None:
                break
            responses.append(response)
        return tuple(responses)

    def pending_count(self) -> int:
        return self._queue.size()
