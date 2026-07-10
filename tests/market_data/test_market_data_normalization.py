"""Unit tests for market data normalization."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from market_data import (
    MarketRecordType,
    map_fields,
    normalize_candle_payload,
    normalize_event_payload,
    normalize_historical_payload,
    normalize_orderbook_payload,
    normalize_quote_payload,
    normalize_tick_payload,
    schema_for_record_type,
)
from tests.market_data_helpers import make_ohlcv_payload


@pytest.mark.unit
def test_map_fields_applies_mapping() -> None:
    payload = {"source_field": "value", "other": 1}
    mapped = map_fields(payload, {"source_field": "target_field"})
    assert mapped == {"target_field": "value"}


@pytest.mark.unit
def test_normalize_candle_payload() -> None:
    timestamp = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    candle = normalize_candle_payload(
        record_id="candle-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        payload=make_ohlcv_payload(close=110.0, timestamp=timestamp),
        sequence=1,
    )
    assert candle.close == 110.0
    assert candle.sequence == 1


@pytest.mark.unit
def test_normalize_tick_payload() -> None:
    tick = normalize_tick_payload(
        record_id="tick-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        payload={"price": 50.0, "size": 3.0},
    )
    assert tick.price == 50.0
    assert tick.size == 3.0


@pytest.mark.unit
def test_normalize_quote_payload() -> None:
    quote = normalize_quote_payload(
        record_id="quote-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        payload={"bid": 99.0, "ask": 101.0},
    )
    assert quote.bid == 99.0
    assert quote.ask == 101.0


@pytest.mark.unit
def test_normalize_event_payload() -> None:
    event = normalize_event_payload(
        record_id="event-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        payload={"event_type": "status", "status": "active"},
    )
    assert event.event_type == "status"
    assert event.payload["status"] == "active"


@pytest.mark.unit
def test_normalize_orderbook_payload() -> None:
    snapshot = normalize_orderbook_payload(
        record_id="book-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        payload={
            "bids": [{"price": 99.0, "size": 1.0}],
            "asks": [{"price": 101.0, "size": 2.0}],
        },
    )
    assert len(snapshot.bids) == 1
    assert len(snapshot.asks) == 1


@pytest.mark.unit
def test_normalize_historical_payload_candle() -> None:
    record = normalize_historical_payload(
        record_id="record-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        payload=make_ohlcv_payload(close=120.0),
        record_type=MarketRecordType.CANDLE,
    )
    assert record.record_type == MarketRecordType.CANDLE
    assert record.attributes["close"] == "120.0"


@pytest.mark.unit
def test_normalize_historical_payload_tick() -> None:
    record = normalize_historical_payload(
        record_id="record-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        payload={"price": 10.0, "size": 1.0},
        record_type=MarketRecordType.TICK,
    )
    assert record.record_type == MarketRecordType.TICK


@pytest.mark.unit
def test_schema_for_record_type_candle() -> None:
    schema = schema_for_record_type(MarketRecordType.CANDLE)
    assert schema.schema_id == "candle-v1"
    assert "close" in schema.required_fields


@pytest.mark.unit
def test_normalize_historical_payload_quote() -> None:
    record = normalize_historical_payload(
        record_id="record-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        payload={"bid": 99.0, "ask": 101.0},
        record_type=MarketRecordType.QUOTE,
    )
    assert record.record_type == MarketRecordType.QUOTE
