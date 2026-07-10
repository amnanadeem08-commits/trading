"""Inference request contract."""

from __future__ import annotations

from typing import Any

from inference_pipeline.requests.inference_options import InferenceOptions
from models.common import PlatformModel


class InferenceRequest(PlatformModel):
    """Request to run inference orchestration for a production model."""

    request_id: str
    model_id: str
    input_metadata: dict[str, Any]
    options: InferenceOptions = InferenceOptions()
    correlation_id: str = ""
    trace_id: str = ""
    tags: tuple[str, ...] = ()
