"""Feature intake DTOs and mappers."""

from __future__ import annotations

from pydantic import Field

from feature_engineering.models.feature_set import FeatureSet
from feature_engineering.models.feature_vector import FeatureVector
from feature_store.models.feature_record import FeatureRecord
from models.common import PlatformModel, UTCDateTime, utc_now
from signal_engine.exceptions import SignalIntakeError


class FeatureIntakePayload(PlatformModel):
    """Named indicator values ready to populate SignalAssemblyRequest."""

    payload_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    indicators_used: tuple[str, ...] = Field(min_length=1)
    indicator_values: dict[str, float | str | int | bool] = Field(min_length=1)
    source_vector_id: str = Field(min_length=1)
    version: str = Field(min_length=1)


def _coerce_store_value(raw: str) -> float | str | int | bool:
    lowered = raw.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def feature_intake_from_vector(vector: FeatureVector) -> FeatureIntakePayload:
    """Map a feature vector into a signal intake payload."""
    if not vector.features:
        raise SignalIntakeError("FeatureVector.features must not be empty")
    indicators_used = tuple(feature.name for feature in vector.features)
    indicator_values: dict[str, float | str | int | bool] = {
        feature.name: feature.value for feature in vector.features
    }
    return FeatureIntakePayload(
        payload_id=vector.vector_id,
        symbol_id=vector.symbol_id,
        dataset_id=vector.dataset_id,
        timestamp=vector.timestamp,
        indicators_used=indicators_used,
        indicator_values=indicator_values,
        source_vector_id=vector.vector_id,
        version=vector.version,
    )


def feature_intake_from_set(
    feature_set: FeatureSet,
    *,
    symbol_id: str | None = None,
) -> tuple[FeatureIntakePayload, ...]:
    """Map feature-set vectors into intake payloads, optionally filtered by symbol."""
    if not feature_set.vectors:
        raise SignalIntakeError("FeatureSet.vectors must not be empty")
    payloads: list[FeatureIntakePayload] = []
    for vector in feature_set.vectors:
        if symbol_id is not None and vector.symbol_id != symbol_id:
            continue
        payloads.append(feature_intake_from_vector(vector))
    if not payloads:
        msg = f"No feature vectors matched symbol_id={symbol_id!r}"
        raise SignalIntakeError(msg)
    return tuple(payloads)


def feature_intake_from_store_record(record: FeatureRecord) -> FeatureIntakePayload:
    """Map a persisted feature-store record into an intake payload."""
    if not record.values:
        raise SignalIntakeError("FeatureRecord.values must not be empty")
    indicator_values = {name: _coerce_store_value(value) for name, value in record.values.items()}
    return FeatureIntakePayload(
        payload_id=record.record_id,
        symbol_id=record.symbol_id,
        dataset_id=record.dataset_id,
        timestamp=record.timestamp,
        indicators_used=tuple(indicator_values),
        indicator_values=indicator_values,
        source_vector_id=record.vector_id,
        version=record.version,
    )
