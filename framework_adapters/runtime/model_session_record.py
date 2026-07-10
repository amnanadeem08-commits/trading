"""Model session record contracts."""

from __future__ import annotations

from pydantic import Field

from framework_adapters.runtime.model_runtime_state import ModelRuntimeState
from models.common import PlatformModel, UTCDateTime


class ModelSessionRecord(PlatformModel):
    """Metadata for a cached adapter-managed model session."""

    session_id: str
    model_id: str
    artifact_id: str
    adapter_id: str
    framework: str
    executor_id: str
    model_version: str = ""
    loaded_at: UTCDateTime | None = None
    last_access_at: UTCDateTime | None = None
    execution_count: int = 0
    reference_count: int = 1
    memory_footprint: dict[str, object] = Field(default_factory=dict)
    state: ModelRuntimeState = ModelRuntimeState.LOADING
    warm: bool = False
    cached: bool = False
    reload_required: bool = False
