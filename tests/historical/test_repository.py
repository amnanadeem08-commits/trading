"""Unit tests for historical repository."""

from __future__ import annotations

import pytest

from historical import DatasetNotFoundError, Repository
from tests.historical_helpers import make_sample_dataset, make_sample_record, seed_repository


def test_repository_register_and_metadata() -> None:
    repository = Repository()
    dataset = make_sample_dataset()
    repository.register_dataset(dataset)
    metadata = repository.metadata("dataset-1")
    assert metadata.dataset_id == "dataset-1"
    assert repository.exists("dataset-1") is False


def test_repository_store_load_list() -> None:
    repository = Repository()
    seed_repository(repository)
    records = repository.load("dataset-1")
    assert len(records) == 3
    assert repository.exists("dataset-1") is True
    assert repository.list() == ("dataset-1",)


def test_repository_version() -> None:
    repository = Repository()
    seed_repository(repository)
    version = repository.version("dataset-1")
    assert version.dataset_id == "dataset-1"
    assert version.version == "1.0.0"


def test_repository_delete() -> None:
    repository = Repository()
    seed_repository(repository)
    repository.delete("dataset-1")
    assert repository.exists("dataset-1") is False
    with pytest.raises(DatasetNotFoundError):
        repository.load("dataset-1")


def test_repository_create_dataset() -> None:
    repository = Repository()
    dataset = repository.create_dataset(
        dataset_id="created-1",
        version="1.0.0",
        name="Created Dataset",
        tags=("created",),
    )
    assert dataset.dataset_id == "created-1"
    assert repository.metadata("created-1").name == "Created Dataset"


def test_repository_store_updates_checksum() -> None:
    repository = Repository()
    repository.register_dataset(make_sample_dataset())
    repository.store(make_sample_record())
    dataset = repository.get_dataset("dataset-1")
    assert dataset.record_count == 1
    assert dataset.checksum != ""
