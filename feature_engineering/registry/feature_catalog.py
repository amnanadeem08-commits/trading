"""Feature catalog metadata."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class FeatureCatalogEntry(PlatformModel):
    """Catalog entry for a registered feature definition."""

    feature_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    extractor_id: str = Field(min_length=1, default="attribute-extractor")
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)
