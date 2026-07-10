"""Unit tests for dataset registry."""

from __future__ import annotations

import pytest

from data import (
    CircularDatasetDependencyError,
    DatasetNotFoundError,
    DatasetRegistrationError,
    DatasetRegistry,
    get_dataset_registry,
    reset_dataset_registry,
)
from tests.data_helpers import RecordsDataset, make_dataset


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_dataset_registry()
    yield
    reset_dataset_registry()


@pytest.mark.unit
def test_registry_register_resolve_list_exists() -> None:
    registry = DatasetRegistry()
    dataset = make_dataset(dataset_id="alpha")
    registry.register(dataset)
    assert registry.exists("alpha") is True
    assert registry.resolve("alpha").dataset_id == "alpha"
    assert registry.list() == ("alpha",)


@pytest.mark.unit
def test_registry_unregister_missing_raises() -> None:
    registry = DatasetRegistry()
    with pytest.raises(DatasetNotFoundError):
        registry.unregister("missing")


@pytest.mark.unit
def test_registry_duplicate_registration_raises() -> None:
    registry = DatasetRegistry()
    dataset = make_dataset(dataset_id="dup")
    registry.register(dataset)
    with pytest.raises(DatasetRegistrationError):
        registry.register(dataset)


@pytest.mark.unit
def test_registry_register_type_and_list_types() -> None:
    registry = DatasetRegistry()
    registry.register_type(RecordsDataset)
    assert registry.list_types() == ("records",)
    assert registry.resolve_type("records") is RecordsDataset


@pytest.mark.unit
def test_registry_validate_set_execution_order() -> None:
    registry = DatasetRegistry()
    records = make_dataset(dataset_id="records")
    derived = make_dataset(dataset_id="derived", dependencies=("records",))
    result = registry.validate_set((derived, records))
    assert result.valid is True
    assert result.execution_order == ("records", "derived")


@pytest.mark.unit
def test_registry_validate_set_cycle_raises() -> None:
    registry = DatasetRegistry()
    first = make_dataset(dataset_id="a", dependencies=("b",))
    second = make_dataset(dataset_id="b", dependencies=("a",))
    with pytest.raises(CircularDatasetDependencyError):
        registry.validate_set((first, second))


@pytest.mark.unit
def test_get_dataset_registry_singleton() -> None:
    assert get_dataset_registry() is get_dataset_registry()


@pytest.mark.unit
def test_registry_unregister_type_missing_raises() -> None:
    registry = DatasetRegistry()
    with pytest.raises(DatasetNotFoundError):
        registry.unregister_type("missing")
