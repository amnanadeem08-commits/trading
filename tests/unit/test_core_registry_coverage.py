"""Additional core registry and identifier coverage."""

from __future__ import annotations

import pytest

from core import (
    EntityNotFoundError,
    EntityRegistrationError,
    EntityRegistry,
    IdentifierError,
    IdManager,
    get_entity_registry,
    reset_entity_registry,
    validate_entity_id,
)
from tests.core_helpers import SampleEntity, make_entity


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_entity_registry()
    yield
    reset_entity_registry()


@pytest.mark.unit
def test_registry_register_type_and_resolve() -> None:
    registry = EntityRegistry()
    registry.register_type(SampleEntity)
    entity_type = registry.resolve_type("sample-entity")
    assert entity_type is SampleEntity
    assert registry.list_types() == ("sample-entity",)


@pytest.mark.unit
def test_registry_unregister_and_unregister_type() -> None:
    registry = EntityRegistry()
    registry.register(make_entity())
    registry.register_type(SampleEntity)
    registry.unregister("sample-entity")
    registry.unregister_type("sample-entity")
    with pytest.raises(EntityNotFoundError):
        registry.resolve("sample-entity")


@pytest.mark.unit
def test_registry_empty_id_raises() -> None:
    registry = EntityRegistry()
    with pytest.raises(EntityRegistrationError):
        registry.register(make_entity(entity_id="   "))


@pytest.mark.unit
def test_registry_validate_set_uses_registered_entities() -> None:
    registry = EntityRegistry()
    registry.register(make_entity(entity_id="base"))
    result = registry.validate_set()
    assert result.valid is True


@pytest.mark.unit
def test_id_manager_register_and_exists() -> None:
    manager = IdManager()
    issued = manager.register("sample-entity")
    assert issued.value == "sample-entity"
    assert manager.exists("sample-entity") is True


@pytest.mark.unit
def test_id_manager_register_duplicate_raises() -> None:
    manager = IdManager()
    manager.register("sample-entity")
    with pytest.raises(IdentifierError):
        manager.register("sample-entity")


@pytest.mark.unit
def test_id_manager_issue_prefix_validation() -> None:
    with pytest.raises(IdentifierError):
        IdManager().issue(prefix="   ")


@pytest.mark.unit
def test_validate_entity_id_rejects_invalid_pattern() -> None:
    with pytest.raises(IdentifierError):
        validate_entity_id("1-invalid")


@pytest.mark.unit
def test_get_entity_registry_singleton() -> None:
    first = get_entity_registry()
    second = get_entity_registry()
    assert first is second
