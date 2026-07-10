"""Feature snapshot contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class FeatureSnapshot(PlatformModel):
    """Point-in-time snapshot of a feature dataset."""

    snapshot_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    record_count: int = Field(ge=0, default=0)
    checksum: str = ""
    lineage: tuple[str, ...] = Field(default_factory=tuple)
    immutable: bool = True
    created_at: UTCDateTime = Field(default_factory=utc_now)
