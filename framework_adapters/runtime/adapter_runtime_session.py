"""Runtime session tracking for loaded adapters."""

from __future__ import annotations

from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.registry.adapter_record import AdapterState
from models.common import PlatformModel, UTCDateTime


class AdapterRuntimeSession(PlatformModel):
    """Tracks adapter load state within a runtime session."""

    session_id: str
    adapter_id: str
    engine_type: EngineType
    state: AdapterState
    created_at: UTCDateTime
    loaded_at: UTCDateTime | None = None
    unloaded_at: UTCDateTime | None = None
