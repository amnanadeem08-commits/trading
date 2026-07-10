"""Historical dataset metadata contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class HistoricalDatasetMetadata(PlatformModel):
    """Descriptive metadata for a historical dataset."""

    dataset_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    source: str = "internal"
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)
    updated_at: UTCDateTime = Field(default_factory=utc_now)
