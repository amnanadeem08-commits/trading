"""Unit tests for core identifiers."""

from __future__ import annotations

import pytest

from core import IdentifierError, IdManager, generate_entity_id, validate_entity_id


@pytest.mark.unit
def test_generate_entity_id_has_prefix() -> None:
    entity_id = generate_entity_id(prefix="resource")
    assert entity_id.startswith("resource-")


@pytest.mark.unit
def test_validate_entity_id_normalizes() -> None:
    assert validate_entity_id(" Sample-Entity ") == "sample-entity"


@pytest.mark.unit
def test_validate_entity_id_rejects_invalid() -> None:
    with pytest.raises(IdentifierError):
        validate_entity_id("")


@pytest.mark.unit
def test_id_manager_issues_unique_ids() -> None:
    manager = IdManager()
    first = manager.issue(prefix="entity")
    second = manager.issue(prefix="entity")
    assert first.value != second.value
    assert len(manager.list()) == 2
