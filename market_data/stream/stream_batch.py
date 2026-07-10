"""Stream batch contracts."""

from __future__ import annotations

from pydantic import Field

from market_data.models.market_record import MarketRecord
from models.common import PlatformModel


class StreamBatch(PlatformModel):
    """Batch of market records from a stream."""

    stream_id: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    offset: int = Field(ge=0, default=0)
    records: tuple[MarketRecord, ...] = Field(default_factory=tuple)
    total: int = Field(ge=0, default=0)
    completed: bool = False
