"""Unit tests for inference scheduler."""

from __future__ import annotations

import pytest

from inference_pipeline import InferenceRequest, InferenceStatus, InferenceValidationError
from tests.inference_pipeline_helpers import make_inference_runtime


@pytest.mark.unit
def test_scheduler_submit_and_run() -> None:
    runtime = make_inference_runtime()
    request = InferenceRequest(
        request_id="req-1",
        model_id="model-1",
        input_metadata={"feature_set_id": "fs-1"},
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    runtime.scheduler.submit(request)
    response = runtime.scheduler.run_next()
    assert response is not None
    assert response.status == InferenceStatus.COMPLETED


@pytest.mark.unit
def test_scheduler_batch_submit() -> None:
    from inference_pipeline import InferenceBatchRequest

    runtime = make_inference_runtime()
    batch = InferenceBatchRequest(
        batch_id="batch-1",
        model_id="model-1",
        input_metadata_batch=({"id": "1"}, {"id": "2"}),
    )
    requests = runtime.scheduler.submit_batch(batch)
    assert len(requests) == 2
    responses = runtime.scheduler.run_all()
    assert len(responses) == 2


@pytest.mark.unit
def test_scheduler_invalid_request_raises() -> None:
    runtime = make_inference_runtime()
    request = InferenceRequest(
        request_id="req-bad",
        model_id="",
        input_metadata={},
    )
    with pytest.raises(InferenceValidationError):
        runtime.scheduler.submit(request)
