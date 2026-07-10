"""Inference context contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from core.context.core_context import CoreContext
from models.common import PlatformModel


class InferenceContext(PlatformModel):
    """Context for an inference operation."""

    inference_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    core_context: CoreContext | None = None
    input_count: int = Field(ge=0, default=0)
    parameters: dict[str, Any] = Field(default_factory=dict)
