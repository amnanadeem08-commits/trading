"""Feature metadata contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class FeatureMetadata(PlatformModel):
    """Metadata describing a feature set or extraction run."""

    feature_set_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    version: str = Field(min_length=1, default="1.0.0")
    extractor_id: str = Field(min_length=1, default="default")
    feature_count: int = Field(ge=0, default=0)
    record_count: int = Field(ge=0, default=0)
    source_id: str = "internal"
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)
