"""Integration tests for feature store pipeline."""

from __future__ import annotations

import pytest

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from tests.feature_engineering_helpers import seed_historical_and_stream


@pytest.mark.integration
def test_historical_to_feature_store_flow() -> None:
    _, stream = seed_historical_and_stream(record_count=3)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    dataset = ingest_feature_set(store, extraction.feature_set)
    records = store.load_offline("dataset-1")

    assert dataset.record_count == 3
    assert len(records) == 3
    assert "close" in records[0].values


@pytest.mark.integration
def test_feature_store_snapshot_and_version() -> None:
    _, stream = seed_historical_and_stream(record_count=2)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    ingest_feature_set(store, extraction.feature_set)
    snapshot = store.create_snapshot("dataset-1")
    version = store.version_registry.latest("dataset-1")

    assert snapshot.snapshot_id == version.snapshot_id
    assert snapshot.record_count == 2


@pytest.mark.integration
def test_feature_store_online_contract() -> None:
    _, stream = seed_historical_and_stream(record_count=1)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    ingest_feature_set(store, extraction.feature_set)
    records = store.load_offline("dataset-1")
    store.put_online("latest:dataset-1", records[0])
    online = store.get_online("latest:dataset-1")
    assert online.record_id == records[0].record_id
