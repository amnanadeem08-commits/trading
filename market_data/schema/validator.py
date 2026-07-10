"""Market data schema validator."""

from __future__ import annotations

from pydantic import Field

from market_data.models.candle import Candle
from market_data.models.market_record import MarketRecord
from market_data.schema.schema import MarketSchema
from models.common import PlatformModel, UTCDateTime


class MarketValidationResult(PlatformModel):
    """Outcome of market data validation."""

    valid: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: tuple[str, ...] = ()


class MarketSchemaValidator:
    """Validates market records and batches against schemas."""

    def validate_record(
        self,
        record: MarketRecord | None,
        *,
        schema: MarketSchema | None = None,
    ) -> MarketValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        checks["record_present"] = record is not None
        if record is None:
            errors.append("Record is required")
            return MarketValidationResult(valid=False, checks=checks, errors=tuple(errors))
        checks["record_id_present"] = bool(record.record_id.strip())
        checks["dataset_id_present"] = bool(record.dataset_id.strip())
        checks["symbol_id_present"] = bool(record.symbol_id.strip())
        if not checks["record_id_present"]:
            errors.append("Record id is required")
        if schema is not None and record.record_type != schema.record_type:
            errors.append("Record type mismatch")
            checks["record_type_match"] = False
        else:
            checks["record_type_match"] = True
        return MarketValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_batch(self, records: tuple[MarketRecord, ...]) -> MarketValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        seen: set[str] = set()
        duplicate = False
        monotonic = True
        previous: UTCDateTime | None = None
        for record in records:
            if record.record_id in seen:
                duplicate = True
                break
            seen.add(record.record_id)
            if previous is not None and record.timestamp < previous:
                monotonic = False
            previous = record.timestamp
        checks["no_duplicates"] = not duplicate
        checks["timestamps_monotonic"] = monotonic
        if duplicate:
            errors.append("Duplicate record ids detected")
        if not monotonic:
            errors.append("Timestamps must be monotonic")
        return MarketValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_candle(self, candle: Candle) -> MarketValidationResult:
        checks: dict[str, bool] = {
            "record_id_present": bool(candle.record_id.strip()),
            "symbol_id_present": bool(candle.symbol_id.strip()),
        }
        errors: list[str] = []
        if candle.high < candle.low:
            errors.append("High must be greater than or equal to low")
            checks["ohlc_bounds"] = False
        else:
            checks["ohlc_bounds"] = True
        return MarketValidationResult(valid=not errors, checks=checks, errors=tuple(errors))
