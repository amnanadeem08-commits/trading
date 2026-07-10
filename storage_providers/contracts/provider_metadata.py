"""Storage provider metadata contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime


class ProviderMetadata(PlatformModel):
    """Metadata describing a storage provider."""

    provider_id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    registered_at: UTCDateTime | None = None
    attributes: dict[str, object] = Field(default_factory=dict)
