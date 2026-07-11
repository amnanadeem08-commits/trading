"""Market intake DTOs and mappers."""

from __future__ import annotations

from pydantic import Field

from market_data.models.candle import Candle
from market_data.models.market_record import MarketRecord, MarketRecordType
from models.common import PlatformModel, UTCDateTime, utc_now
from signal_engine.exceptions import SignalIntakeError


class MarketIntakeFrame(PlatformModel):
    """Normalised market snapshot ready for signal assembly provenance."""

    frame_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    record_type: str = Field(min_length=1)
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    sequence: int = Field(ge=0, default=0)
    source_id: str = Field(min_length=1, default="market_data")
    ohlcv: dict[str, float] = Field(default_factory=dict)
    raw_attributes: dict[str, str] = Field(default_factory=dict)


def market_intake_from_candle(
    candle: Candle,
    *,
    market_id: str | None = None,
    source_id: str = "market_data",
) -> MarketIntakeFrame:
    """Map a candle into a market intake frame."""
    resolved_market_id = market_id if market_id is not None else candle.dataset_id
    if not resolved_market_id.strip():
        raise SignalIntakeError("market_id must not be empty")
    return MarketIntakeFrame(
        frame_id=candle.record_id,
        symbol_id=candle.symbol_id,
        dataset_id=candle.dataset_id,
        market_id=resolved_market_id,
        record_type=MarketRecordType.CANDLE.value,
        timestamp=candle.timestamp,
        sequence=candle.sequence,
        source_id=source_id,
        ohlcv={
            "open": float(candle.open),
            "high": float(candle.high),
            "low": float(candle.low),
            "close": float(candle.close),
            "volume": float(candle.volume),
        },
        raw_attributes={},
    )


def market_intake_from_record(
    record: MarketRecord,
    *,
    market_id: str | None = None,
) -> MarketIntakeFrame:
    """Map a generic market record into a market intake frame."""
    resolved_market_id = market_id if market_id is not None else record.dataset_id
    if not resolved_market_id.strip():
        raise SignalIntakeError("market_id must not be empty")
    ohlcv: dict[str, float] = {}
    for key in ("open", "high", "low", "close", "volume"):
        raw = record.attributes.get(key)
        if raw is None:
            continue
        try:
            ohlcv[key] = float(raw)
        except ValueError as error:
            msg = f"Invalid OHLCV attribute '{key}': {raw}"
            raise SignalIntakeError(msg) from error
    return MarketIntakeFrame(
        frame_id=record.record_id,
        symbol_id=record.symbol_id,
        dataset_id=record.dataset_id,
        market_id=resolved_market_id,
        record_type=record.record_type.value,
        timestamp=record.timestamp,
        sequence=record.sequence,
        source_id=record.source_id,
        ohlcv=ohlcv,
        raw_attributes=dict(record.attributes),
    )
