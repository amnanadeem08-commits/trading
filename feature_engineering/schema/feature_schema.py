"""Feature schema contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class FeatureSchema(PlatformModel):
    """Schema definition for feature vectors."""

    schema_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    required_fields: tuple[str, ...] = Field(default_factory=tuple)
    optional_fields: tuple[str, ...] = Field(default_factory=tuple)
    version: str = Field(min_length=1, default="1.0.0")
    description: str = ""
