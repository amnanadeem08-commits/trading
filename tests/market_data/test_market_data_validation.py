"""Unit tests for market data validation."""

from __future__ import annotations

import pytest

from market_data import MarketSchemaValidator
from market_data.schema.schema import MarketSchema
from tests.market_data_helpers import make_sample_candle, make_sample_market_record


@pytest.mark.unit
def test_validate_record_success() -> None:
    validator = MarketSchemaValidator()
    record = make_sample_market_record()
    result = validator.validate_record(record)
    assert result.valid is True
    assert result.checks["record_present"] is True


@pytest.mark.unit
def test_validate_record_missing_record() -> None:
    validator = MarketSchemaValidator()
    result = validator.validate_record(None)
    assert result.valid is False
    assert "Record is required" in result.errors


@pytest.mark.unit
def test_validate_record_type_mismatch() -> None:
    validator = MarketSchemaValidator()
    record = make_sample_market_record()
    schema = MarketSchema(schema_id="tick-v1", record_type=record.record_type)
    result = validator.validate_record(record, schema=schema)
    assert result.valid is True


@pytest.mark.unit
def test_validate_batch_monotonic_timestamps() -> None:
    validator = MarketSchemaValidator()
    first = make_sample_market_record(record_id="record-1", sequence=0)
    second = make_sample_market_record(record_id="record-2", sequence=1)
    result = validator.validate_batch((first, second))
    assert result.valid is True
    assert result.checks["timestamps_monotonic"] is True


@pytest.mark.unit
def test_validate_batch_detects_duplicates() -> None:
    validator = MarketSchemaValidator()
    record = make_sample_market_record(record_id="duplicate")
    result = validator.validate_batch((record, record))
    assert result.valid is False
    assert "Duplicate record ids detected" in result.errors


@pytest.mark.unit
def test_validate_candle_bounds() -> None:
    validator = MarketSchemaValidator()
    candle = make_sample_candle()
    result = validator.validate_candle(candle)
    assert result.valid is True
    assert result.checks["ohlc_bounds"] is True


@pytest.mark.unit
def test_validate_candle_rejects_invalid_bounds() -> None:
    validator = MarketSchemaValidator()
    candle = make_sample_candle()
    invalid = candle.model_copy(update={"high": 1.0, "low": 10.0})
    result = validator.validate_candle(invalid)
    assert result.valid is False
    assert result.checks["ohlc_bounds"] is False


@pytest.mark.unit
def test_validate_batch_non_monotonic_timestamps() -> None:
    validator = MarketSchemaValidator()
    from datetime import UTC, datetime

    later_ts = datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC)
    earlier_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    later = make_sample_candle(record_id="later", sequence=1, timestamp=later_ts)
    earlier = make_sample_candle(record_id="earlier", sequence=0, timestamp=earlier_ts)
    result = validator.validate_batch((later.to_market_record(), earlier.to_market_record()))
    assert result.valid is False
    assert "Timestamps must be monotonic" in result.errors
