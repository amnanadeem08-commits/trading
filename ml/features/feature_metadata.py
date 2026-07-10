"""Feature metadata contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class FeatureMetadata(PlatformModel):
    """Metadata describing a feature set."""

    feature_set_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source_dataset_id: str = Field(min_length=1)
    field_count: int = Field(ge=0, default=0)
    attributes: dict[str, str] = Field(default_factory=dict)
