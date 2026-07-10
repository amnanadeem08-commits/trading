"""Unit tests for historical dataset contracts."""

from __future__ import annotations

import pytest

from historical import HistoricalDataset, compute_dataset_checksum
from tests.historical_helpers import make_sample_dataset


def test_historical_dataset_fields() -> None:
    dataset = make_sample_dataset()
    assert dataset.dataset_id == "dataset-1"
    assert dataset.version == "1.0.0"
    assert dataset.metadata.name == "Sample Dataset"
    assert "timestamp" in dataset.dataset_schema.fields


def test_historical_dataset_with_helpers() -> None:
    dataset = make_sample_dataset().with_record_count(5).with_checksum("abc")
    assert dataset.record_count == 5
    assert dataset.checksum == "abc"


def test_compute_dataset_checksum_stable() -> None:
    records = ({"value": 1}, {"value": 2})
    first = compute_dataset_checksum(records)
    second = compute_dataset_checksum(records)
    assert first == second
    assert len(first) == 64


def test_historical_dataset_requires_id() -> None:
    with pytest.raises(ValueError):
        HistoricalDataset(
            dataset_id="",
            version="1.0.0",
            metadata=make_sample_dataset().metadata,
        )
