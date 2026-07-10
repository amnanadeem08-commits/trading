"""Paper execution record contracts."""

from __future__ import annotations

from pydantic import Field

from connectors.adapters.paper.paper_order_state import PaperState
from models.common import PlatformModel, UTCDateTime, utc_now


class PaperExecutionRecord(PlatformModel):
    """In-memory record for a simulated execution operation."""

    record_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    state: PaperState = PaperState.NEW
    created_at: UTCDateTime = Field(default_factory=utc_now)
    updated_at: UTCDateTime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)
