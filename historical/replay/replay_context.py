"""Replay context contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime


class ReplayContext(PlatformModel):
    """Configuration for a replay session."""

    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    deterministic: bool = True
    start_timestamp: UTCDateTime | None = None
    end_timestamp: UTCDateTime | None = None
    window_size: int = Field(ge=1, default=1)
    correlation_id: str = "historical-replay"
    trace_id: str = "historical-replay"
