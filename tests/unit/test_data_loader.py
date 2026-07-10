"""Unit tests for dataset loader."""

from __future__ import annotations

import pytest

from data import DatasetLoadError, InMemoryDatasetLoader
from tests.data_helpers import DerivedDataset, RecordsDataset, make_dataset


@pytest.mark.unit
def test_in_memory_loader_loads_records() -> None:
    implementation = RecordsDataset()
    loader = InMemoryDatasetLoader({implementation.dataset_id(): implementation})
    dataset = make_dataset(dataset_id="records")
    result = loader.load(dataset)
    assert result.status.value == "completed"
    assert result.record_count == 2


@pytest.mark.unit
def test_in_memory_loader_load_records() -> None:
    implementation = RecordsDataset()
    loader = InMemoryDatasetLoader({implementation.dataset_id(): implementation})
    records = loader.load_records("records")
    assert len(records) == 2
    assert records[0]["id"] == "1"


@pytest.mark.unit
def test_in_memory_loader_missing_implementation_raises() -> None:
    loader = InMemoryDatasetLoader()
    dataset = make_dataset(dataset_id="missing")
    with pytest.raises(DatasetLoadError):
        loader.load(dataset)


@pytest.mark.unit
def test_in_memory_loader_register_implementation() -> None:
    loader = InMemoryDatasetLoader()
    implementation = DerivedDataset()
    loader.register_implementation(implementation)
    records = loader.load_records("derived")
    assert len(records) == 1
