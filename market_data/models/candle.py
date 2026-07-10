"""Candle record contract."""

from __future__ import annotations

from pydantic import Field

from market_data.models.market_record import MarketRecord, MarketRecordType
from models.common import PlatformModel, UTCDateTime, utc_now


class Candle(PlatformModel):
    """Generic OHLCV-style candle record."""

    record_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = Field(ge=0.0, default=0.0)
    sequence: int = Field(ge=0, default=0)

    def to_market_record(self) -> MarketRecord:
        """Convert to a generic market record."""
        return MarketRecord(
            record_id=self.record_id,
            dataset_id=self.dataset_id,
            symbol_id=self.symbol_id,
            record_type=MarketRecordType.CANDLE,
            timestamp=self.timestamp,
            sequence=self.sequence,
            attributes={
                "open": str(self.open),
                "high": str(self.high),
                "low": str(self.low),
                "close": str(self.close),
                "volume": str(self.volume),
            },
        )
