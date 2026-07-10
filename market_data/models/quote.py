"""Quote record contract."""

from __future__ import annotations

from pydantic import Field

from market_data.models.market_record import MarketRecord, MarketRecordType
from models.common import PlatformModel, UTCDateTime, utc_now


class Quote(PlatformModel):
    """Generic quote record."""

    record_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    bid: float = 0.0
    ask: float = 0.0
    bid_size: float = Field(ge=0.0, default=0.0)
    ask_size: float = Field(ge=0.0, default=0.0)
    sequence: int = Field(ge=0, default=0)

    def to_market_record(self) -> MarketRecord:
        """Convert to a generic market record."""
        return MarketRecord(
            record_id=self.record_id,
            dataset_id=self.dataset_id,
            symbol_id=self.symbol_id,
            record_type=MarketRecordType.QUOTE,
            timestamp=self.timestamp,
            sequence=self.sequence,
            attributes={
                "bid": str(self.bid),
                "ask": str(self.ask),
                "bid_size": str(self.bid_size),
                "ask_size": str(self.ask_size),
            },
        )
