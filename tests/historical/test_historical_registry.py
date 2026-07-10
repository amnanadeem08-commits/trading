"""Unit tests for historical dataset registry."""

from __future__ import annotations

import pytest

from historical import (
    DatasetRegistrationError,
    DatasetRegistry,
    HistoricalRegistry,
)
from tests.historical_helpers import make_sample_dataset, seed_repository


def test_dataset_registry_register_resolve() -> None:
    registry = DatasetRegistry()
    dataset = make_sample_dataset()
    registry.register(dataset)
    resolved = registry.resolve("dataset-1")
    assert resolved.dataset_id == "dataset-1"
    assert registry.list() == ("dataset-1",)


def test_dataset_registry_duplicate_raises() -> None:
    registry = DatasetRegistry()
    dataset = make_sample_dataset()
    registry.register(dataset)
    with pytest.raises(DatasetRegistrationError):
        registry.register(dataset)


def test_historical_registry_coordinates_components() -> None:
    registry = HistoricalRegistry()
    repository = registry.repository
    seed_repository(repository)
    dataset = make_sample_dataset()
    registry.register(dataset)
    assert registry.exists("dataset-1") is True
    assert registry.query.lookup_by_id("dataset-1").matched is True
    assert registry.replay is not None
