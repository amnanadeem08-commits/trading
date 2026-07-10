"""Unit tests for core registry."""

from __future__ import annotations

import pytest

from core import EntityNotFoundError, EntityRegistrationError, EntityRegistry
from tests.core_helpers import make_entity


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    from core import reset_entity_registry

    reset_entity_registry()
    yield
    reset_entity_registry()


@pytest.mark.unit
def test_registry_register_and_resolve() -> None:
    registry = EntityRegistry()
    entity = make_entity()
    registry.register(entity)
    resolved = registry.resolve("sample-entity")
    assert resolved.entity_id == "sample-entity"
    assert registry.list() == ("sample-entity",)


@pytest.mark.unit
def test_registry_duplicate_registration_raises() -> None:
    registry = EntityRegistry()
    registry.register(make_entity())
    with pytest.raises(EntityRegistrationError):
        registry.register(make_entity())


@pytest.mark.unit
def test_registry_resolve_missing_raises() -> None:
    registry = EntityRegistry()
    with pytest.raises(EntityNotFoundError):
        registry.resolve("missing")
