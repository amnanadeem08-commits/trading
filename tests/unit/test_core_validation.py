"""Unit tests for core validation."""

from __future__ import annotations

import pytest

from core import CircularEntityDependencyError, validate_entity_set
from tests.core_helpers import DerivedEntity, SampleEntity, make_entity


@pytest.mark.unit
def test_validate_entity_set_success() -> None:
    entities = (
        make_entity(entity_id="base"),
        make_entity(entity_id="derived", dependencies=("base",)),
    )
    result = validate_entity_set(entities)
    assert result.valid is True
    assert result.load_order == ("base", "derived")


@pytest.mark.unit
def test_validate_entity_set_detects_missing_dependency() -> None:
    entities = (make_entity(entity_id="derived", dependencies=("missing",)),)
    result = validate_entity_set(entities)
    assert result.valid is False
    assert any("Missing dependency" in error for error in result.errors)


@pytest.mark.unit
def test_validate_entity_set_detects_cycle() -> None:
    entities = (
        make_entity(entity_id="a", dependencies=("b",)),
        make_entity(entity_id="b", dependencies=("a",)),
    )
    with pytest.raises(CircularEntityDependencyError):
        validate_entity_set(entities)


@pytest.mark.unit
def test_validate_entity_set_detects_duplicate_ids() -> None:
    entities = (
        make_entity(entity_id="dup"),
        make_entity(entity_id="dup"),
    )
    result = validate_entity_set(entities)
    assert result.valid is False
    assert "Duplicate entity identifiers" in result.errors[0]


@pytest.mark.unit
def test_validate_entity_set_detects_self_dependency() -> None:
    entities = (make_entity(entity_id="self", dependencies=("self",)),)
    result = validate_entity_set(entities)
    assert result.valid is False
    assert any("depends on itself" in error for error in result.errors)


@pytest.mark.unit
def test_validate_entity_set_detects_empty_entity_type() -> None:
    entity = make_entity(entity_id="typed")
    invalid = entity.model_copy(update={"entity_type": ""})
    result = validate_entity_set((invalid,))
    assert result.valid is False
    assert any("Entity type must not be empty" in error for error in result.errors)


@pytest.mark.unit
def test_base_entity_to_definition() -> None:
    definition = SampleEntity().to_definition()
    assert definition.entity_id == "sample-entity"
    assert DerivedEntity().dependencies() == ("sample-entity",)
    assert definition.metadata["scope"] == "test"
