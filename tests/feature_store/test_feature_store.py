"""Unit tests for feature store facade."""

from __future__ import annotations

import pytest

from feature_store import ingest_feature_set
from feature_store.exceptions import DatasetNotFoundError
from tests.feature_store_helpers import (
    make_feature_dataset,
    make_feature_record,
    make_feature_store,
    seed_feature_set_from_pipeline,
)


@pytest.mark.unit
def test_register_and_ingest_dataset() -> None:
    store = make_feature_store()
    feature_set, _ = seed_feature_set_from_pipeline(record_count=2)
    dataset = ingest_feature_set(store, feature_set)
    assert dataset.record_count == 2
    assert store.exists("dataset-1") is True


@pytest.mark.unit
def test_offline_retrieval() -> None:
    store = make_feature_store()
    feature_set, _ = seed_feature_set_from_pipeline(record_count=3)
    ingest_feature_set(store, feature_set)
    records = store.load_offline("dataset-1")
    assert len(records) == 3


@pytest.mark.unit
def test_online_retrieval() -> None:
    store = make_feature_store()
    store.register_dataset(make_feature_dataset())
    record = make_feature_record(record_id="online-1")
    store.ingest_records((record,))
    store.put_online("dataset-1:online-1", record)
    resolved = store.get_online("dataset-1:online-1")
    assert resolved.record_id == "online-1"


@pytest.mark.unit
def test_create_snapshot() -> None:
    store = make_feature_store()
    feature_set, _ = seed_feature_set_from_pipeline(record_count=2)
    ingest_feature_set(store, feature_set)
    snapshot = store.create_snapshot("dataset-1")
    assert snapshot.record_count == 2
    assert snapshot.dataset_id == "dataset-1"


@pytest.mark.unit
def test_validate_dataset() -> None:
    store = make_feature_store()
    feature_set, _ = seed_feature_set_from_pipeline(record_count=2)
    ingest_feature_set(store, feature_set)
    result = store.validate_dataset("dataset-1")
    assert result.valid is True


@pytest.mark.unit
def test_lookup_feature() -> None:
    store = make_feature_store()
    feature_set, _ = seed_feature_set_from_pipeline(record_count=1)
    ingest_feature_set(store, feature_set)
    records = store.load_offline("dataset-1")
    resolved = store.lookup_feature(records[0].record_id, dataset_id="dataset-1")
    assert resolved.vector_id == records[0].vector_id


@pytest.mark.unit
def test_metadata_and_version() -> None:
    store = make_feature_store()
    store.register_dataset(make_feature_dataset(version="1.2.0"))
    assert store.version("dataset-1") == "1.2.0"
    assert store.metadata("dataset-1").schema_id == "feature-schema-v1"


@pytest.mark.unit
def test_register_rejects_empty_dataset_id() -> None:
    store = make_feature_store()
    dataset = make_feature_dataset(dataset_id=" ")
    from feature_store.exceptions import DatasetRegistrationError

    with pytest.raises(DatasetRegistrationError):
        store.register_dataset(dataset)


@pytest.mark.unit
def test_missing_dataset_offline_raises() -> None:
    store = make_feature_store()
    with pytest.raises(DatasetNotFoundError):
        store.load_offline("missing")


@pytest.mark.unit
def test_list_datasets() -> None:
    store = make_feature_store()
    store.register_dataset(make_feature_dataset())
    assert store.list_datasets() == ("dataset-1",)


@pytest.mark.unit
def test_store_properties() -> None:
    store = make_feature_store()
    assert store.repository is not None
    assert store.cache is not None
    assert store.dataset_registry is not None
    assert store.validator is not None
