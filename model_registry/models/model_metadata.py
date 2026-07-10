"""Model metadata contract."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime


class ModelMetadata(PlatformModel):
    """Metadata describing a registered model."""

    model_id: str
    name: str
    description: str = ""
    owner: str = "platform"
    tags: tuple[str, ...] = ()
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: UTCDateTime
    updated_at: UTCDateTime
