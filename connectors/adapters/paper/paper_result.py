"""Paper execution result contracts."""

from __future__ import annotations

from pydantic import Field

from connectors.adapters.paper.paper_order_state import PaperState
from models.common import PlatformModel, UTCDateTime, utc_now


class PaperExecutionResult(PlatformModel):
    """Outcome of a simulated paper execution dispatch."""

    execution_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    status: PaperState = PaperState.COMPLETED
    latency_ms: int = Field(ge=0, default=0)
    duration_ms: int = Field(ge=0, default=0)
    metadata: dict[str, str] = Field(default_factory=dict)
    validation_passed: bool = True
    started_at: UTCDateTime = Field(default_factory=utc_now)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
    synthetic_fill: dict[str, object] = Field(default_factory=dict)
