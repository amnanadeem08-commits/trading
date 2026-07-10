"""Stream result contracts."""

from __future__ import annotations

from pydantic import Field

from market_data.models.market_record import MarketRecord
from models.common import PlatformModel


class StreamResult(PlatformModel):
    """Outcome of a stream read operation."""

    stream_id: str = Field(min_length=1)
    offset: int = Field(ge=0, default=0)
    position: int = Field(ge=0, default=0)
    total: int = Field(ge=0, default=0)
    record: MarketRecord | None = None
    completed: bool = False
