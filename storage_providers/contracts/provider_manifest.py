"""Storage provider manifest contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel
from storage_providers.contracts.provider_capability import ProviderCapability
from storage_providers.contracts.provider_type import ProviderType


class ProviderManifest(PlatformModel):
    """Declarative manifest for a storage provider."""

    provider_id: str
    name: str
    version: str
    provider_type: ProviderType = ProviderType.CUSTOM
    supported_uri_schemes: tuple[str, ...] = ()
    capabilities: tuple[ProviderCapability, ...] = ()
    limits: dict[str, object] = Field(default_factory=dict)
    attributes: dict[str, object] = Field(default_factory=dict)
