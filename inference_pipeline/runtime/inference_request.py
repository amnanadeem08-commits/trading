"""Execution request contract for the inference pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from inference_pipeline.requests.inference_options import InferenceOptions
from inference_pipeline.runtime.input_schema import InputSchema
from models.common import PlatformModel


class InferenceExecutionRequest(PlatformModel):
    """Request to execute inference with schema-driven feature binding."""

    request_id: str
    model_id: str
    input_schema: InputSchema
    features: dict[str, Any]
    adapter_id: str = ""
    artifact_id: str = ""
    feature_version: str = "1.0.0"
    options: InferenceOptions = InferenceOptions()
    correlation_id: str = ""
    trace_id: str = ""
    execution_attributes: dict[str, Any] = Field(default_factory=dict)
