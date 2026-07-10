"""Historical query filters."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime


class QueryFilters(PlatformModel):
    """Filter criteria for historical queries."""

    dataset_id: str | None = None
    version: str | None = None
    tags: tuple[str, ...] = Field(default_factory=tuple)
    source: str | None = None
    start_timestamp: UTCDateTime | None = None
    end_timestamp: UTCDateTime | None = None
    cursor_position: int | None = Field(default=None, ge=0)
    metadata_key: str | None = None
    metadata_value: str | None = None
