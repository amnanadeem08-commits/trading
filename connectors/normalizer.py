"""Raw-to-normalized market data transformation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from connectors.exceptions import NormalizationError
from models.market import NormalizedBar


def _ensure_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)


def normalize_bar(
    *,
    timestamp: datetime,
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: float,
    symbol_id: str,
    market_id: str,
    timeframe: str,
) -> NormalizedBar:
    """Normalize explicit OHLCV fields into a NormalizedBar."""
    try:
        return NormalizedBar(
            timestamp=_ensure_utc(timestamp),
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
            symbol_id=symbol_id,
            market_id=market_id,
            timeframe=timeframe,
        )
    except (TypeError, ValueError) as error:
        msg = f"Failed to normalize bar for {symbol_id}: {error}"
        raise NormalizationError(msg, market_id=market_id) from error


def normalize_bar_mapping(
    record: Mapping[str, Any],
    *,
    symbol_id: str,
    market_id: str,
    timeframe: str,
    timestamp_key: str = "timestamp",
    open_key: str = "open",
    high_key: str = "high",
    low_key: str = "low",
    close_key: str = "close",
    volume_key: str = "volume",
) -> NormalizedBar:
    """Normalize a mapping of raw OHLCV fields into a NormalizedBar."""
    missing = [
        key
        for key in (timestamp_key, open_key, high_key, low_key, close_key, volume_key)
        if key not in record
    ]
    if missing:
        msg = f"Missing required fields for normalization: {', '.join(missing)}"
        raise NormalizationError(msg, market_id=market_id, field=missing[0])

    timestamp_value = record[timestamp_key]
    if not isinstance(timestamp_value, datetime):
        msg = f"Field '{timestamp_key}' must be a datetime"
        raise NormalizationError(msg, market_id=market_id, field=timestamp_key)

    numeric_fields = {
        open_key: "open",
        high_key: "high",
        low_key: "low",
        close_key: "close",
        volume_key: "volume",
    }
    numeric_values: dict[str, float] = {}
    for source_key, target_name in numeric_fields.items():
        value = record[source_key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            msg = f"Field '{source_key}' must be numeric"
            raise NormalizationError(msg, market_id=market_id, field=source_key)
        numeric_values[target_name] = float(value)

    return normalize_bar(
        timestamp=timestamp_value,
        open_price=numeric_values["open"],
        high=numeric_values["high"],
        low=numeric_values["low"],
        close=numeric_values["close"],
        volume=numeric_values["volume"],
        symbol_id=symbol_id,
        market_id=market_id,
        timeframe=timeframe,
    )


def normalize_bars(
    records: Iterable[Mapping[str, Any]],
    *,
    symbol_id: str,
    market_id: str,
    timeframe: str,
) -> tuple[NormalizedBar, ...]:
    """Normalize an iterable of raw OHLCV mappings into NormalizedBar objects."""
    return tuple(
        normalize_bar_mapping(
            record,
            symbol_id=symbol_id,
            market_id=market_id,
            timeframe=timeframe,
        )
        for record in records
    )
