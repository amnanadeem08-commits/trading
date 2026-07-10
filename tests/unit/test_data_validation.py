"""Unit tests for dataset validation."""

from __future__ import annotations

import pytest

from data import (
    CircularDatasetDependencyError,
    SchemaValidator,
    validate_dataset,
    validate_dataset_set,
)
from data.schema import SchemaField
from tests.data_helpers import make_dataset, make_schema


@pytest.mark.unit
def test_validate_dataset_success() -> None:
    result = validate_dataset(make_dataset())
    assert result.valid is True
    assert result.errors == ()


@pytest.mark.unit
def test_validate_dataset_empty_id_fails() -> None:
    dataset = make_dataset(dataset_id=" ")
    result = validate_dataset(dataset)
    assert result.valid is False
    assert any("empty" in error for error in result.errors)


@pytest.mark.unit
def test_validate_dataset_metadata_mismatch() -> None:
    dataset = make_dataset(dataset_id="alpha")
    broken = dataset.model_copy(
        update={"metadata": dataset.metadata.model_copy(update={"dataset_id": "beta"})}
    )
    result = validate_dataset(broken)
    assert result.valid is False
    assert any("mismatch" in error for error in result.errors)


@pytest.mark.unit
def test_validate_dataset_self_dependency() -> None:
    dataset = make_dataset(dataset_id="self", dependencies=("self",))
    result = validate_dataset(dataset)
    assert result.valid is False
    assert any("depends on itself" in error for error in result.errors)


@pytest.mark.unit
def test_validate_dataset_set_missing_dependency() -> None:
    dataset = make_dataset(dataset_id="child", dependencies=("parent",))
    result = validate_dataset_set((dataset,))
    assert result.valid is False
    assert any("Missing dependency" in error for error in result.errors)


@pytest.mark.unit
def test_validate_dataset_set_duplicate_ids() -> None:
    first = make_dataset(dataset_id="dup")
    second = make_dataset(dataset_id="dup", name="Other")
    result = validate_dataset_set((first, second))
    assert result.valid is False
    assert any("Duplicate" in error for error in result.errors)


@pytest.mark.unit
def test_validate_dataset_set_cycle_raises() -> None:
    first = make_dataset(dataset_id="a", dependencies=("b",))
    second = make_dataset(dataset_id="b", dependencies=("a",))
    with pytest.raises(CircularDatasetDependencyError):
        validate_dataset_set((first, second))


@pytest.mark.unit
def test_schema_validator_record_validation() -> None:
    schema = make_schema()
    validator = SchemaValidator(schema)
    valid = validator.validate_record({"id": "1", "value": 10})
    assert valid.valid is True
    invalid = validator.validate_record({"id": "1"})
    assert invalid.valid is False


@pytest.mark.unit
def test_schema_duplicate_fields_detected() -> None:
    schema = make_schema().model_copy(
        update={
            "fields": (
                SchemaField(name="id", field_type="string"),
                SchemaField(name="id", field_type="integer"),
            )
        }
    )
    dataset = make_dataset().model_copy(update={"dataset_schema": schema})
    result = validate_dataset(dataset)
    assert result.valid is False
    assert any("Duplicate schema fields" in error for error in result.errors)


@pytest.mark.unit
def test_schema_validate_record_types() -> None:
    schema = make_schema()
    errors = schema.validate_record({"id": "1", "value": "bad"})
    assert any("expected type" in error for error in errors)
