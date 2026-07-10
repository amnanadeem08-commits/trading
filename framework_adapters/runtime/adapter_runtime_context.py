"""Runtime context for adapter selection and routing."""

from __future__ import annotations

from pydantic import Field

from framework_adapters.contracts.engine_type import EngineType
from models.common import PlatformModel


class AdapterRuntimeContext(PlatformModel):
    """Selection and routing context for the adapter runtime."""

    engine_type: EngineType
    artifact_format: str = ""
    artifact_reference: str = ""
    model_id: str = ""
    model_version: str = ""
    runtime_version: str = ""
    executor_id: str = ""
    attributes: dict[str, object] = Field(default_factory=dict)
