"""Feature store metadata contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class FeatureMetadata(PlatformModel):
    """Metadata describing a feature store dataset."""

    dataset_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    version: str = Field(min_length=1, default="1.0.0")
    source_pipeline: str = "feature-pipeline"
    lineage: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)
    updated_at: UTCDateTime = Field(default_factory=utc_now)
