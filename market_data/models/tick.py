"""Tick record contract."""

from __future__ import annotations

from pydantic import Field

from market_data.models.market_record import MarketRecord, MarketRecordType
from models.common import PlatformModel, UTCDateTime, utc_now


class Tick(PlatformModel):
    """Generic tick record."""

    record_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    price: float = 0.0
    size: float = Field(ge=0.0, default=0.0)
    sequence: int = Field(ge=0, default=0)

    def to_market_record(self) -> MarketRecord:
        """Convert to a generic market record."""
        return MarketRecord(
            record_id=self.record_id,
            dataset_id=self.dataset_id,
            symbol_id=self.symbol_id,
            record_type=MarketRecordType.TICK,
            timestamp=self.timestamp,
            sequence=self.sequence,
            attributes={"price": str(self.price), "size": str(self.size)},
        )
