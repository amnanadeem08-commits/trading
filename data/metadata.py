"""Dataset metadata definitions."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class DatasetMetadata(PlatformModel):
    """Descriptive metadata for a dataset."""

    dataset_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)
    owner: str = ""
    created_at: UTCDateTime = Field(default_factory=utc_now)
    updated_at: UTCDateTime = Field(default_factory=utc_now)
    attributes: dict[str, Any] = Field(default_factory=dict)
