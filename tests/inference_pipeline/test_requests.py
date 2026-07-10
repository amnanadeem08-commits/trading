"""Unit tests for inference requests."""

from __future__ import annotations

import pytest

from inference_pipeline import InferenceBatchRequest, InferenceOptions, InferenceRequest


@pytest.mark.unit
def test_inference_request_contract() -> None:
    request = InferenceRequest(
        request_id="req-1",
        model_id="model-1",
        input_metadata={"feature_set_id": "fs-1"},
        options=InferenceOptions(timeout_seconds=30),
    )
    assert request.model_id == "model-1"
    assert request.options.timeout_seconds == 30


@pytest.mark.unit
def test_inference_batch_request() -> None:
    batch = InferenceBatchRequest(
        batch_id="batch-1",
        model_id="model-1",
        input_metadata_batch=({"id": "1"}, {"id": "2"}),
    )
    assert len(batch.input_metadata_batch) == 2
