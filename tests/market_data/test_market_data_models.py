"""Unit tests for market data models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from market_data import (
    Candle,
    EventRecord,
    MarketRecord,
    MarketRecordType,
    OrderBookSnapshot,
    Quote,
    Tick,
)
from market_data.exceptions import MarketNormalizationError
from market_data.schema.normalization import normalize_timestamp
from tests.market_data_helpers import make_sample_candle, make_sample_market_record


@pytest.mark.unit
def test_market_record_fields() -> None:
    record = make_sample_market_record()
    assert record.record_type == MarketRecordType.CANDLE
    assert record.dataset_id == "dataset-1"
    assert record.symbol_id == "symbol-1"


@pytest.mark.unit
def test_candle_to_market_record() -> None:
    candle = make_sample_candle(close=105.0)
    record = candle.to_market_record()
    assert record.record_type == MarketRecordType.CANDLE
    assert record.attributes["close"] == "105.0"
    assert record.attributes["volume"] == "10.0"


@pytest.mark.unit
def test_tick_to_market_record() -> None:
    tick = Tick(
        record_id="tick-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        price=101.5,
        size=2.0,
    )
    record = tick.to_market_record()
    assert record.record_type == MarketRecordType.TICK
    assert record.attributes["price"] == "101.5"


@pytest.mark.unit
def test_quote_to_market_record() -> None:
    quote = Quote(
        record_id="quote-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        bid=99.0,
        ask=101.0,
    )
    record = quote.to_market_record()
    assert record.record_type == MarketRecordType.QUOTE
    assert record.attributes["bid"] == "99.0"


@pytest.mark.unit
def test_event_record_to_market_record() -> None:
    event = EventRecord(
        record_id="event-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        event_type="status",
        payload={"status": "active"},
    )
    record = event.to_market_record()
    assert record.record_type == MarketRecordType.EVENT
    assert record.attributes["event_type"] == "status"


@pytest.mark.unit
def test_orderbook_snapshot_to_market_record() -> None:
    snapshot = OrderBookSnapshot(
        record_id="book-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
    )
    record = snapshot.to_market_record()
    assert record.record_type == MarketRecordType.ORDERBOOK_SNAPSHOT
    assert record.attributes["bid_levels"] == "0"


@pytest.mark.unit
def test_normalize_timestamp_from_datetime() -> None:
    value = datetime(2026, 1, 1, tzinfo=UTC)
    normalized = normalize_timestamp(value)
    assert normalized.tzinfo is UTC


@pytest.mark.unit
def test_normalize_timestamp_from_string() -> None:
    normalized = normalize_timestamp("2026-01-01T12:00:00Z")
    assert normalized.year == 2026


@pytest.mark.unit
def test_normalize_timestamp_rejects_invalid_value() -> None:
    with pytest.raises(MarketNormalizationError):
        normalize_timestamp(123)


@pytest.mark.unit
def test_market_record_type_values() -> None:
    assert MarketRecordType.CANDLE.value == "candle"
    assert MarketRecordType.TICK.value == "tick"
    assert MarketRecordType.QUOTE.value == "quote"
    assert MarketRecordType.ORDERBOOK_SNAPSHOT.value == "orderbook_snapshot"
    assert MarketRecordType.EVENT.value == "event"


@pytest.mark.unit
def test_candle_model_fields() -> None:
    fields = set(Candle.model_fields)
    assert {
        "record_id",
        "dataset_id",
        "symbol_id",
        "open",
        "high",
        "low",
        "close",
        "volume",
    } <= fields


@pytest.mark.unit
def test_market_record_model_fields() -> None:
    fields = set(MarketRecord.model_fields)
    assert {
        "record_id",
        "dataset_id",
        "symbol_id",
        "record_type",
        "timestamp",
        "sequence",
    } <= fields
