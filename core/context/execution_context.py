"""Execution context contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class ExecutionContext(PlatformModel):
    """Context describing runtime execution metadata."""

    execution_id: str = Field(min_length=1)
    runtime_name: str = Field(min_length=1, default="core")
    started_at: UTCDateTime = Field(default_factory=utc_now)
    configuration_hash: str = Field(min_length=1, default="")
    schema_version: str = Field(min_length=1, default="1.0.0")
    feature_flags: dict[str, bool] = Field(default_factory=dict)
