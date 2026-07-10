"""Market catalog metadata."""

from __future__ import annotations

from pydantic import Field

from market_data.models.market_record import MarketRecordType
from models.common import PlatformModel, UTCDateTime, utc_now


class MarketCatalogEntry(PlatformModel):
    """Catalog entry for a registered market dataset."""

    dataset_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    record_type: MarketRecordType = MarketRecordType.CANDLE
    symbol_id: str = Field(min_length=1)
    source_id: str = "internal"
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)
