"""Adapter manifest contracts."""

from __future__ import annotations

from pydantic import Field

from framework_adapters.contracts.adapter_capability import AdapterCapability
from framework_adapters.contracts.engine_type import EngineType
from models.common import PlatformModel


class AdapterManifest(PlatformModel):
    """Declarative manifest for a framework adapter."""

    adapter_id: str
    name: str
    version: str
    author: str = ""
    description: str = ""
    engine_type: EngineType = EngineType.STUB
    framework_requirements: tuple[str, ...] = ()
    supported_artifact_formats: tuple[str, ...] = ()
    supported_runtime_versions: tuple[str, ...] = ()
    capabilities: tuple[AdapterCapability, ...] = ()
    entrypoint: str = ""
    attributes: dict[str, object] = Field(default_factory=dict)
