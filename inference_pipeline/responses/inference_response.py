"""Inference response contract."""

from __future__ import annotations

from inference_pipeline.responses.inference_metadata import InferenceMetadata
from inference_pipeline.responses.inference_result import InferenceStatus
from models.common import PlatformModel


class InferenceResponse(PlatformModel):
    """Response envelope for inference orchestration. No prediction values."""

    request_id: str
    model_id: str
    status: InferenceStatus
    metadata: InferenceMetadata
    message: str = "orchestration completed"
