"""Adapter summary contracts."""

from __future__ import annotations

from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.registry.adapter_record import AdapterState
from models.common import PlatformModel


class AdapterSummary(PlatformModel):
    """Summary record for a framework adapter."""

    adapter_id: str
    name: str
    version: str
    state: AdapterState
    engine_type: EngineType
