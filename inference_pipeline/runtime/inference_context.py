"""Inference context contract."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from model_registry.models.model_version import ModelVersion
from model_registry.models.registered_model import RegisteredModel
from models.common import PlatformModel, UTCDateTime, utc_now


class InferenceContext(PlatformModel):
    """Runtime context for an inference orchestration run."""

    request_id: str
    model: RegisteredModel
    version: ModelVersion
    artifact_id: str
    config_hash: str
    input_metadata: dict[str, Any]
    correlation_id: str
    trace_id: str


class InferenceExecutionContext(PlatformModel):
    """Execution context for a single model inference run."""

    request_id: str
    model_id: str
    artifact_id: str
    adapter_id: str
    runtime_session_id: str = ""
    feature_version: str = "1.0.0"
    execution_timestamp: UTCDateTime = Field(default_factory=utc_now)
    correlation_id: str = ""
    trace_id: str = ""
