"""Market data resolution for prediction validation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from market_data.models.candle import Candle
from prediction_validation.exceptions import LookAheadValidationError


def ordered_candles(candles: Sequence[Candle]) -> tuple[Candle, ...]:
    return tuple(sorted(candles, key=lambda candle: (candle.timestamp, candle.sequence)))


def resolve_outcome_candle(
    candles: Sequence[Candle],
    *,
    validation_due_at: datetime,
    as_of: datetime,
) -> Candle | None:
    """Return the first candle at or after due time that is also available by as_of."""
    if as_of < validation_due_at:
        return None
    for candle in ordered_candles(candles):
        if candle.timestamp < validation_due_at:
            continue
        if candle.timestamp > as_of:
            msg = (
                f"Look-ahead blocked: candle timestamp {candle.timestamp.isoformat()} "
                f"is after as_of {as_of.isoformat()}"
            )
            raise LookAheadValidationError(msg)
        return candle
    return None
