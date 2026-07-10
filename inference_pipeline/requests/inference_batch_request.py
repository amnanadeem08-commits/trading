"""Batch inference request contract."""

from __future__ import annotations

from typing import Any

from inference_pipeline.requests.inference_options import InferenceOptions
from models.common import PlatformModel


class InferenceBatchRequest(PlatformModel):
    """Batch inference orchestration request."""

    batch_id: str
    model_id: str
    input_metadata_batch: tuple[dict[str, Any], ...]
    options: InferenceOptions = InferenceOptions()
    correlation_id: str = ""
    trace_id: str = ""
    tags: tuple[str, ...] = ()
