"""Historical dataset version metadata."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class DatasetVersion(PlatformModel):
    """Version metadata for a historical dataset."""

    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    snapshot_id: str = Field(min_length=1)
    record_count: int = Field(ge=0, default=0)
    checksum: str = ""
    created_at: UTCDateTime = Field(default_factory=utc_now)
    immutable: bool = True
