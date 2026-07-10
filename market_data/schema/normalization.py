"""Market data normalization utilities."""

from __future__ import annotations

from datetime import UTC, datetime

from market_data.exceptions import MarketNormalizationError
from market_data.models.candle import Candle
from market_data.models.event_record import EventRecord
from market_data.models.market_record import MarketRecord, MarketRecordType
from market_data.models.orderbook_snapshot import BookLevel, OrderBookSnapshot
from market_data.models.quote import Quote
from market_data.models.tick import Tick
from market_data.schema.schema import MarketSchema
from models.common import UTCDateTime


def _as_float(value: object, default: float = 0.0) -> float:
    """Coerce a payload value to float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value)
    return default


def _iter_book_levels(raw: object) -> tuple[dict[str, object], ...]:
    """Return iterable book level dictionaries from a payload value."""
    if not isinstance(raw, (list, tuple)):
        return ()
    levels: list[dict[str, object]] = []
    for item in raw:
        if isinstance(item, dict):
            levels.append(item)
    return tuple(levels)


def normalize_timestamp(value: object) -> UTCDateTime:
    """Normalize a timestamp value to UTC."""
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed
    msg = f"Unsupported timestamp value: {value!r}"
    raise MarketNormalizationError(msg)


def map_fields(payload: dict[str, object], mapping: dict[str, str]) -> dict[str, object]:
    """Map payload fields using a generic field mapping."""
    mapped: dict[str, object] = {}
    for source, target in mapping.items():
        if source in payload:
            mapped[target] = payload[source]
    return mapped


def normalize_candle_payload(
    *,
    record_id: str,
    dataset_id: str,
    symbol_id: str,
    payload: dict[str, object],
    sequence: int = 0,
) -> Candle:
    """Normalize a payload dictionary into a candle record."""
    timestamp = normalize_timestamp(payload.get("timestamp", datetime.now(UTC)))
    return Candle(
        record_id=record_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        timestamp=timestamp,
        open=_as_float(payload.get("open", 0.0)),
        high=_as_float(payload.get("high", 0.0)),
        low=_as_float(payload.get("low", 0.0)),
        close=_as_float(payload.get("close", payload.get("value", 0.0))),
        volume=_as_float(payload.get("volume", 0.0)),
        sequence=sequence,
    )


def normalize_tick_payload(
    *,
    record_id: str,
    dataset_id: str,
    symbol_id: str,
    payload: dict[str, object],
    sequence: int = 0,
) -> Tick:
    """Normalize a payload dictionary into a tick record."""
    timestamp = normalize_timestamp(payload.get("timestamp", datetime.now(UTC)))
    return Tick(
        record_id=record_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        timestamp=timestamp,
        price=_as_float(payload.get("price", payload.get("value", 0.0))),
        size=_as_float(payload.get("size", 0.0)),
        sequence=sequence,
    )


def normalize_quote_payload(
    *,
    record_id: str,
    dataset_id: str,
    symbol_id: str,
    payload: dict[str, object],
    sequence: int = 0,
) -> Quote:
    """Normalize a payload dictionary into a quote record."""
    timestamp = normalize_timestamp(payload.get("timestamp", datetime.now(UTC)))
    return Quote(
        record_id=record_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        timestamp=timestamp,
        bid=_as_float(payload.get("bid", 0.0)),
        ask=_as_float(payload.get("ask", 0.0)),
        bid_size=_as_float(payload.get("bid_size", 0.0)),
        ask_size=_as_float(payload.get("ask_size", 0.0)),
        sequence=sequence,
    )


def normalize_event_payload(
    *,
    record_id: str,
    dataset_id: str,
    symbol_id: str,
    payload: dict[str, object],
    sequence: int = 0,
) -> EventRecord:
    """Normalize a payload dictionary into an event record."""
    timestamp = normalize_timestamp(payload.get("timestamp", datetime.now(UTC)))
    event_type = str(payload.get("event_type", "generic"))
    event_payload = {
        key: value for key, value in payload.items() if key not in {"timestamp", "event_type"}
    }
    return EventRecord(
        record_id=record_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        timestamp=timestamp,
        event_type=event_type,
        payload=event_payload,
        sequence=sequence,
    )


def normalize_orderbook_payload(
    *,
    record_id: str,
    dataset_id: str,
    symbol_id: str,
    payload: dict[str, object],
    sequence: int = 0,
) -> OrderBookSnapshot:
    """Normalize a payload dictionary into an order book snapshot."""
    timestamp = normalize_timestamp(payload.get("timestamp", datetime.now(UTC)))
    bids_raw = _iter_book_levels(payload.get("bids", ()))
    asks_raw = _iter_book_levels(payload.get("asks", ()))
    bids = tuple(
        BookLevel(price=_as_float(item.get("price", 0.0)), size=_as_float(item.get("size", 0.0)))
        for item in bids_raw
    )
    asks = tuple(
        BookLevel(price=_as_float(item.get("price", 0.0)), size=_as_float(item.get("size", 0.0)))
        for item in asks_raw
    )
    return OrderBookSnapshot(
        record_id=record_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        timestamp=timestamp,
        bids=bids,
        asks=asks,
        sequence=sequence,
    )


def normalize_historical_payload(
    *,
    record_id: str,
    dataset_id: str,
    symbol_id: str,
    payload: dict[str, object],
    sequence: int = 0,
    record_type: MarketRecordType = MarketRecordType.CANDLE,
) -> MarketRecord:
    """Normalize a historical repository payload into a market record."""
    if record_type == MarketRecordType.CANDLE:
        return normalize_candle_payload(
            record_id=record_id,
            dataset_id=dataset_id,
            symbol_id=symbol_id,
            payload=payload,
            sequence=sequence,
        ).to_market_record()
    if record_type == MarketRecordType.TICK:
        return normalize_tick_payload(
            record_id=record_id,
            dataset_id=dataset_id,
            symbol_id=symbol_id,
            payload=payload,
            sequence=sequence,
        ).to_market_record()
    if record_type == MarketRecordType.QUOTE:
        return normalize_quote_payload(
            record_id=record_id,
            dataset_id=dataset_id,
            symbol_id=symbol_id,
            payload=payload,
            sequence=sequence,
        ).to_market_record()
    if record_type == MarketRecordType.EVENT:
        return normalize_event_payload(
            record_id=record_id,
            dataset_id=dataset_id,
            symbol_id=symbol_id,
            payload=payload,
            sequence=sequence,
        ).to_market_record()
    if record_type == MarketRecordType.ORDERBOOK_SNAPSHOT:
        return normalize_orderbook_payload(
            record_id=record_id,
            dataset_id=dataset_id,
            symbol_id=symbol_id,
            payload=payload,
            sequence=sequence,
        ).to_market_record()
    msg = f"Unsupported record type: {record_type}"
    raise MarketNormalizationError(msg)


def schema_for_record_type(record_type: MarketRecordType) -> MarketSchema:
    """Return a default schema for a record type."""
    if record_type == MarketRecordType.CANDLE:
        return MarketSchema(
            schema_id="candle-v1",
            record_type=record_type,
            required_fields=("timestamp", "open", "high", "low", "close", "volume"),
        )
    if record_type == MarketRecordType.TICK:
        return MarketSchema(
            schema_id="tick-v1",
            record_type=record_type,
            required_fields=("timestamp", "price", "size"),
        )
    return MarketSchema(schema_id=f"{record_type.value}-v1", record_type=record_type)
