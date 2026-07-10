"""Event record contract."""

from __future__ import annotations

from pydantic import Field

from market_data.models.market_record import MarketRecord, MarketRecordType
from models.common import PlatformModel, UTCDateTime, utc_now


class EventRecord(PlatformModel):
    """Generic event-style market record."""

    record_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    event_type: str = Field(min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)
    sequence: int = Field(ge=0, default=0)

    def to_market_record(self) -> MarketRecord:
        """Convert to a generic market record."""
        return MarketRecord(
            record_id=self.record_id,
            dataset_id=self.dataset_id,
            symbol_id=self.symbol_id,
            record_type=MarketRecordType.EVENT,
            timestamp=self.timestamp,
            sequence=self.sequence,
            attributes={"event_type": self.event_type},
        )
