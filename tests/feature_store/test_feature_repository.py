"""Unit tests for feature repository."""

from __future__ import annotations

import pytest

from feature_store import FeatureRepository
from feature_store.exceptions import DatasetNotFoundError, FeatureRecordNotFoundError
from tests.feature_store_helpers import make_feature_dataset, make_feature_record


@pytest.mark.unit
def test_store_and_load_records() -> None:
    repository = FeatureRepository()
    repository.register_dataset(make_feature_dataset())
    repository.store(make_feature_record(record_id="record-1"))
    repository.store(make_feature_record(record_id="record-2"))
    records = repository.load("dataset-1")
    assert len(records) == 2


@pytest.mark.unit
def test_lookup_record() -> None:
    repository = FeatureRepository()
    repository.register_dataset(make_feature_dataset())
    repository.store(make_feature_record(record_id="record-lookup"))
    record = repository.lookup("record-lookup", dataset_id="dataset-1")
    assert record.record_id == "record-lookup"


@pytest.mark.unit
def test_create_snapshot() -> None:
    repository = FeatureRepository()
    repository.register_dataset(make_feature_dataset())
    repository.store(make_feature_record())
    snapshot = repository.create_snapshot("dataset-1")
    assert snapshot.record_count == 1


@pytest.mark.unit
def test_checksum_updated_on_store() -> None:
    repository = FeatureRepository()
    repository.register_dataset(make_feature_dataset())
    repository.store(make_feature_record())
    dataset = repository.get_dataset("dataset-1")
    assert dataset.checksum != ""


@pytest.mark.unit
def test_missing_record_raises() -> None:
    repository = FeatureRepository()
    repository.register_dataset(make_feature_dataset())
    with pytest.raises(FeatureRecordNotFoundError):
        repository.lookup("missing", dataset_id="dataset-1")


@pytest.mark.unit
def test_missing_dataset_raises() -> None:
    repository = FeatureRepository()
    with pytest.raises(DatasetNotFoundError):
        repository.get_dataset("missing")


@pytest.mark.unit
def test_delete_dataset() -> None:
    repository = FeatureRepository()
    repository.register_dataset(make_feature_dataset())
    repository.delete("dataset-1")
    with pytest.raises(DatasetNotFoundError):
        repository.get_dataset("dataset-1")


@pytest.mark.unit
def test_list_snapshots_and_get_snapshot() -> None:
    repository = FeatureRepository()
    repository.register_dataset(make_feature_dataset())
    repository.store(make_feature_record())
    snapshot = repository.create_snapshot("dataset-1")
    snapshots = repository.list_snapshots("dataset-1")
    assert len(snapshots) == 1
    assert repository.get_snapshot(snapshot.snapshot_id).snapshot_id == snapshot.snapshot_id


@pytest.mark.unit
def test_load_with_version_filter() -> None:
    repository = FeatureRepository()
    repository.register_dataset(make_feature_dataset(version="1.0.0"))
    repository.store(make_feature_record(record_id="r1", dataset_id="dataset-1"))
    record_v2 = make_feature_record(record_id="r2", dataset_id="dataset-1").model_copy(
        update={"version": "2.0.0"}
    )
    repository.store(record_v2)
    filtered = repository.load("dataset-1", version="2.0.0")
    assert len(filtered) == 1
    assert filtered[0].version == "2.0.0"


@pytest.mark.unit
def test_store_without_dataset_raises() -> None:
    repository = FeatureRepository()
    with pytest.raises(DatasetNotFoundError):
        repository.store(make_feature_record())


@pytest.mark.unit
def test_get_snapshot_missing_raises() -> None:
    from feature_store.exceptions import SnapshotNotFoundError

    repository = FeatureRepository()
    with pytest.raises(SnapshotNotFoundError):
        repository.get_snapshot("missing")
