"""Unit tests for dataset repository."""

from __future__ import annotations

import pytest

from data import DatasetNotFoundError, InMemoryDatasetRepository
from tests.data_helpers import make_dataset


@pytest.mark.unit
def test_repository_add_get_list() -> None:
    repository = InMemoryDatasetRepository()
    dataset = make_dataset(dataset_id="alpha")
    repository.add(dataset)
    assert repository.get("alpha").dataset_id == "alpha"
    assert repository.list() == ("alpha",)
    assert len(repository.all()) == 1


@pytest.mark.unit
def test_repository_get_missing_raises() -> None:
    repository = InMemoryDatasetRepository()
    with pytest.raises(DatasetNotFoundError):
        repository.get("missing")


@pytest.mark.unit
def test_repository_remove() -> None:
    repository = InMemoryDatasetRepository()
    dataset = make_dataset(dataset_id="alpha")
    repository.add(dataset)
    repository.remove("alpha")
    assert repository.list() == ()


@pytest.mark.unit
def test_repository_remove_missing_raises() -> None:
    repository = InMemoryDatasetRepository()
    with pytest.raises(DatasetNotFoundError):
        repository.remove("missing")
