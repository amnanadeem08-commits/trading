"""Pipeline request contract."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import Field

from models.common import PlatformModel, ReproducibilityKey


class PipelineRequest(PlatformModel):
    """Immutable pipeline execution request."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    configuration_hash: str = Field(min_length=1)
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    reproducibility_key: ReproducibilityKey
