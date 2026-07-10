"""Helpers for market data framework tests."""

from __future__ import annotations

from datetime import UTC, datetime

from historical import Repository
from market_data import (
    Candle,
    MarketCatalogEntry,
    MarketRecord,
    MarketRecordType,
    StreamContext,
)
from models.common import utc_now
from tests.historical_helpers import make_sample_dataset, seed_repository


def make_sample_candle(
    *,
    record_id: str = "candle-1",
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
    sequence: int = 0,
    close: float = 100.0,
    timestamp: datetime | None = None,
) -> Candle:
    resolved_timestamp = timestamp or utc_now()
    return Candle(
        record_id=record_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        timestamp=resolved_timestamp,
        open=close - 1.0,
        high=close + 1.0,
        low=close - 2.0,
        close=close,
        volume=10.0,
        sequence=sequence,
    )


def make_sample_market_record(
    *,
    record_id: str = "record-1",
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
    record_type: MarketRecordType = MarketRecordType.CANDLE,
    sequence: int = 0,
) -> MarketRecord:
    candle = make_sample_candle(
        record_id=record_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        sequence=sequence,
    )
    market_record = candle.to_market_record()
    if record_type != MarketRecordType.CANDLE:
        return market_record.model_copy(update={"record_type": record_type})
    return market_record


def make_catalog_entry(
    *,
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
    version: str = "1.0.0",
) -> MarketCatalogEntry:
    return MarketCatalogEntry(
        dataset_id=dataset_id,
        name="Sample Market Dataset",
        version=version,
        symbol_id=symbol_id,
        source_id="test",
        capabilities=("normalize", "stream"),
        tags=("sample",),
    )


def make_stream_context(
    *,
    stream_id: str = "stream-1",
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
    buffer_size: int = 100,
    batch_size: int = 10,
) -> StreamContext:
    return StreamContext(
        stream_id=stream_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        buffer_size=buffer_size,
        batch_size=batch_size,
    )


def seed_market_repository(repository: Repository, *, record_count: int = 3) -> Repository:
    seed_repository(repository, record_count=record_count)
    return repository


def make_timestamp_sequence(count: int) -> tuple[datetime, ...]:
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    return tuple(base.replace(minute=index) for index in range(count))


def make_ohlcv_payload(
    *,
    close: float = 100.0,
    timestamp: datetime | None = None,
) -> dict[str, object]:
    resolved_timestamp = timestamp or utc_now()
    return {
        "timestamp": resolved_timestamp.isoformat(),
        "open": close - 1.0,
        "high": close + 1.0,
        "low": close - 2.0,
        "close": close,
        "volume": 10.0,
    }


def register_sample_dataset(repository: Repository) -> None:
    repository.register_dataset(make_sample_dataset())
