"""Generic market record contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class MarketRecordType(StrEnum):
    """Supported generic market record types."""

    CANDLE = "candle"
    TICK = "tick"
    QUOTE = "quote"
    ORDERBOOK_SNAPSHOT = "orderbook_snapshot"
    EVENT = "event"


class MarketRecord(PlatformModel):
    """Base contract for standardized market-style records."""

    record_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    record_type: MarketRecordType
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    version: str = Field(min_length=1, default="1.0.0")
    source_id: str = "internal"
    sequence: int = Field(ge=0, default=0)
    attributes: dict[str, str] = Field(default_factory=dict)
