"""Provider summary contracts."""

from __future__ import annotations

from models.common import PlatformModel
from storage_providers.contracts.provider_type import ProviderType
from storage_providers.registry.provider_record import ProviderState


class ProviderSummary(PlatformModel):
    """Summary snapshot for a storage provider."""

    provider_id: str
    name: str
    version: str
    state: ProviderState
    provider_type: ProviderType
    uri_scheme: str = ""
