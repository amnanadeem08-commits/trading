"""Market data contracts. Market-agnostic normalized types."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from models.common import PlatformModel, UTCDateTime


class AssetClass(StrEnum):
    """Classification of tradable asset."""

    COMMODITY = "commodity"
    CRYPTO = "crypto"
    EQUITY = "equity"
    FOREX = "forex"
    FUTURES = "futures"
    INDEX = "index"


class HealthStatus(StrEnum):
    """Connector or service health state."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Symbol(PlatformModel):
    """Canonical symbol representation."""

    symbol_id: str = Field(min_length=1, description="Canonical symbol identifier")
    market_id: str = Field(min_length=1, description="Connector market identifier")
    display_name: str | None = None
    asset_class: AssetClass
    base_asset: str | None = None
    quote_asset: str | None = None
    is_active: bool = True


class SymbolFilter(PlatformModel):
    """Optional filters for symbol universe queries."""

    asset_class: AssetClass | None = None
    is_active: bool | None = None
    limit: int | None = Field(default=None, ge=1)


class NormalizedBar(PlatformModel):
    """Normalized OHLCV bar. All connectors must produce this shape."""

    timestamp: UTCDateTime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1, description="Candle interval, e.g. 1m, 4h, 1d")

    @model_validator(mode="after")
    def validate_ohlc_consistency(self) -> NormalizedBar:
        if self.high < self.low:
            msg = "high must be >= low"
            raise ValueError(msg)
        if self.high < max(self.open, self.close):
            msg = "high must be >= open and close"
            raise ValueError(msg)
        if self.low > min(self.open, self.close):
            msg = "low must be <= open and close"
            raise ValueError(msg)
        return self


class NormalizedTicker(PlatformModel):
    """Normalized live ticker snapshot."""

    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    last: float | None = Field(default=None, ge=0)
    volume_24h: float | None = Field(default=None, ge=0)
    timestamp: UTCDateTime


class MarketMetadata(PlatformModel):
    """Market-specific metadata normalized for platform consumption."""

    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    asset_class: AssetClass
    timezone: str = Field(min_length=1, description="IANA timezone for presentation only")
    session_hours: str | None = Field(
        default=None,
        description="Human-readable session description",
    )
    tick_size: float = Field(gt=0)
    lot_size: float = Field(gt=0)
    min_order_size: float = Field(gt=0)
    supports_sentiment: bool = False
    candle_intervals: tuple[str, ...] = Field(min_length=1)


class RawMarketRecord(PlatformModel):
    """Staging record from connector before data intelligence processing."""

    market_id: str = Field(min_length=1)
    connector_version: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    payload: dict[str, Any]
    ingested_at: UTCDateTime
