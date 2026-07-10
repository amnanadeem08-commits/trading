"""Adapter metadata contracts."""

from __future__ import annotations

from pydantic import Field

from framework_adapters.contracts.engine_type import EngineType
from models.common import PlatformModel, UTCDateTime


class AdapterMetadata(PlatformModel):
    """Metadata for a framework adapter."""

    adapter_id: str
    name: str
    version: str
    author: str = ""
    description: str = ""
    engine_type: EngineType = EngineType.STUB
    registered_at: UTCDateTime | None = None
    attributes: dict[str, object] = Field(default_factory=dict)
