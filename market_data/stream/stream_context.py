"""Stream context contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class StreamContext(PlatformModel):
    """Configuration for an in-memory market data stream."""

    stream_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    buffer_size: int = Field(ge=1, default=100)
    batch_size: int = Field(ge=1, default=10)
    offset: int = Field(ge=0, default=0)
    window_size: int = Field(ge=1, default=1)
    correlation_id: str = "market-stream"
    trace_id: str = "market-stream"
