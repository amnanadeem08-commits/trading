"""ML model metadata contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class ModelMetadata(PlatformModel):
    """Metadata describing a registered ML model."""

    model_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    framework: str = Field(min_length=1, default="platform")
    description: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
