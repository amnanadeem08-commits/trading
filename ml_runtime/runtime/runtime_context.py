"""Runtime execution context."""

from __future__ import annotations

from models.common import PlatformModel


class RuntimeContext(PlatformModel):
    """Execution context passed to model executors."""

    session_id: str
    request_id: str
    model_id: str
    model_version: str
    artifact_reference: str
    executor_id: str
    input_metadata: dict[str, object]
    correlation_id: str
    trace_id: str
    config_hash: str = ""
    checksum: str = ""
