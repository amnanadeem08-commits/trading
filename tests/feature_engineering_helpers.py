"""Helpers for feature engineering tests."""

from __future__ import annotations

from feature_engineering import (
    Feature,
    FeatureCatalogEntry,
    FeatureExtractionContext,
    FeatureSchema,
    FeatureVector,
)
from market_data import StreamBuffer, StreamContext
from models.common import utc_now
from tests.historical_helpers import seed_repository
from tests.market_data_helpers import make_sample_candle


def make_extraction_context(
    *,
    pipeline_id: str = "pipeline-1",
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
    schema_id: str = "feature-schema-v1",
    batch_size: int = 10,
) -> FeatureExtractionContext:
    return FeatureExtractionContext(
        pipeline_id=pipeline_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        schema_id=schema_id,
        batch_size=batch_size,
    )


def make_sample_feature_vector(
    *,
    vector_id: str = "vector-1",
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
    record_id: str = "record-1",
) -> FeatureVector:
    return FeatureVector(
        vector_id=vector_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        record_id=record_id,
        features=(
            Feature(name="close", value=100.0, dtype="float", source_field="close"),
            Feature(name="volume", value=10.0, dtype="float", source_field="volume"),
        ),
        timestamp=utc_now(),
    )


def make_feature_schema(
    *,
    schema_id: str = "feature-schema-v1",
    required_fields: tuple[str, ...] = ("close", "volume"),
) -> FeatureSchema:
    return FeatureSchema(
        schema_id=schema_id,
        name="Sample Feature Schema",
        required_fields=required_fields,
        optional_fields=("open", "high", "low"),
    )


def make_catalog_entry(
    *,
    feature_id: str = "feature-1",
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
) -> FeatureCatalogEntry:
    return FeatureCatalogEntry(
        feature_id=feature_id,
        name="Sample Feature",
        schema_id="feature-schema-v1",
        version="1.0.0",
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        capabilities=("extract", "validate"),
        tags=("sample",),
    )


def make_stream_buffer_from_candles(
    *,
    record_count: int = 3,
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
) -> StreamBuffer:
    records = tuple(
        make_sample_candle(
            record_id=f"record-{index + 1}",
            dataset_id=dataset_id,
            symbol_id=symbol_id,
            sequence=index,
            close=100.0 + index,
        ).to_market_record()
        for index in range(record_count)
    )
    context = StreamContext(
        stream_id="stream-1",
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        buffer_size=max(100, len(records)),
        batch_size=10,
    )
    return StreamBuffer(context, records)


def seed_historical_and_stream(*, record_count: int = 3):
    from historical import HistoricalRegistry

    historical = HistoricalRegistry()
    seed_repository(historical.repository, record_count=record_count)
    from market_data import build_stream_from_repository

    stream = build_stream_from_repository(
        historical.repository,
        dataset_id="dataset-1",
        symbol_id="symbol-1",
    )
    return historical, stream
