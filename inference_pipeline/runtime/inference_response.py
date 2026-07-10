"""Execution response contract for the inference pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from inference_pipeline.responses.inference_response import InferenceResponse
from inference_pipeline.responses.inference_result import InferenceStatus
from models.common import PlatformModel, UTCDateTime


class InferenceExecutionResponse(PlatformModel):
    """Framework-independent execution response with normalized output."""

    request_id: str
    model_id: str
    status: InferenceStatus
    orchestration_response: InferenceResponse
    normalized_output: dict[str, Any]
    execution_attributes: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    total_latency_ms: float = 0.0
    feature_mapping_ms: float = 0.0
    input_binding_ms: float = 0.0
    execution_latency_ms: float = 0.0
    normalization_ms: float = 0.0
    completed_at: UTCDateTime | None = None
