"""Helpers for feature store tests."""

from __future__ import annotations

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureDataset, FeatureMetadata, FeatureRecord, FeatureStore
from models.common import utc_now
from tests.feature_engineering_helpers import seed_historical_and_stream


def make_feature_metadata(
    *,
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
    schema_id: str = "feature-schema-v1",
) -> FeatureMetadata:
    return FeatureMetadata(
        dataset_id=dataset_id,
        name="Sample Feature Dataset",
        schema_id=schema_id,
        symbol_id=symbol_id,
        source_pipeline="feature-pipeline",
        lineage=("dataset-1",),
        tags=("sample",),
    )


def make_feature_dataset(
    *,
    dataset_id: str = "dataset-1",
    version: str = "1.0.0",
    symbol_id: str = "symbol-1",
) -> FeatureDataset:
    return FeatureDataset(
        dataset_id=dataset_id,
        version=version,
        metadata=make_feature_metadata(dataset_id=dataset_id, symbol_id=symbol_id),
        lineage=("dataset-1", "feature-pipeline"),
        tags=("sample",),
    )


def make_feature_record(
    *,
    record_id: str = "record-1",
    dataset_id: str = "dataset-1",
    symbol_id: str = "symbol-1",
    close: str = "100.0",
) -> FeatureRecord:
    return FeatureRecord(
        record_id=record_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        vector_id=f"vector-{record_id}",
        source_record_id=f"source-{record_id}",
        timestamp=utc_now(),
        values={"close": close, "volume": "10.0"},
    )


def make_feature_store() -> FeatureStore:
    return FeatureStore()


def seed_feature_set_from_pipeline(*, record_count: int = 3):
    _, stream = seed_historical_and_stream(record_count=record_count)
    result = run_extraction_from_stream(stream, max_batches=1)
    assert result.feature_set is not None
    return result.feature_set, stream
