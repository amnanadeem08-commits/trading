"""Repository record contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class RepositoryRecord(PlatformModel):
    """Stored historical record."""

    record_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    payload: dict[str, object] = Field(default_factory=dict)
    sequence: int = Field(ge=0, default=0)
