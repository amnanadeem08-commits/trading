"""Unit tests for dataset registry."""

from __future__ import annotations

import pytest

from feature_store import DatasetRegistry
from feature_store.exceptions import DatasetNotFoundError, DatasetRegistrationError
from tests.feature_store_helpers import make_feature_dataset


@pytest.mark.unit
def test_register_and_lookup() -> None:
    registry = DatasetRegistry()
    dataset = make_feature_dataset()
    registry.register(dataset)
    resolved = registry.lookup("dataset-1")
    assert resolved.version == "1.0.0"


@pytest.mark.unit
def test_register_rejects_empty_id() -> None:
    registry = DatasetRegistry()
    dataset = make_feature_dataset(dataset_id=" ")
    with pytest.raises(DatasetRegistrationError):
        registry.register(dataset)


@pytest.mark.unit
def test_list_versions() -> None:
    registry = DatasetRegistry()
    registry.register(make_feature_dataset(version="1.0.0"))
    registry.register(make_feature_dataset(version="1.1.0"))
    versions = registry.list_versions("dataset-1")
    assert versions == ("1.0.0", "1.1.0")


@pytest.mark.unit
def test_missing_dataset_raises() -> None:
    registry = DatasetRegistry()
    with pytest.raises(DatasetNotFoundError):
        registry.lookup("missing")
