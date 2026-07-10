"""Unit tests for dataset selector."""

from __future__ import annotations

import pytest

from tests.training_pipeline_helpers import seed_feature_store_with_dataset
from training_pipeline import DatasetReferenceError, DatasetSelector


@pytest.mark.unit
def test_dataset_selector_resolve_reference() -> None:
    store = seed_feature_store_with_dataset()
    selector = DatasetSelector(store)
    reference = selector.resolve_reference(dataset_id="dataset-1")
    assert reference.dataset_id == "dataset-1"
    assert reference.record_count == 3


@pytest.mark.unit
def test_dataset_selector_capture_snapshot() -> None:
    store = seed_feature_store_with_dataset(record_count=2)
    selector = DatasetSelector(store)
    snapshot = selector.capture_snapshot("dataset-1")
    assert snapshot.dataset_id == "dataset-1"
    assert snapshot.record_count == 2


@pytest.mark.unit
def test_dataset_selector_missing_dataset_raises() -> None:
    store = seed_feature_store_with_dataset()
    selector = DatasetSelector(store)
    with pytest.raises(DatasetReferenceError):
        selector.resolve_reference(dataset_id="missing")
