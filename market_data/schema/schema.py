"""Market data schema contracts."""

from __future__ import annotations

from pydantic import Field

from market_data.models.market_record import MarketRecordType
from models.common import PlatformModel


class MarketSchema(PlatformModel):
    """Schema definition for market data records."""

    schema_id: str = Field(min_length=1)
    record_type: MarketRecordType
    required_fields: tuple[str, ...] = Field(default_factory=tuple)
    optional_fields: tuple[str, ...] = Field(default_factory=tuple)
    timestamp_field: str = "timestamp"
