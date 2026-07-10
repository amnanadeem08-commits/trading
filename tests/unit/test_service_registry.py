"""Unit tests for service registry."""

from __future__ import annotations

import pytest

from services import (
    CircularDependencyError,
    ServiceNotFoundError,
    ServiceRegistrationError,
    ServiceRegistry,
    get_service_registry,
    reset_service_registry,
)
from tests.services_fixtures import AlphaService, BetaService


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_service_registry()
    yield
    reset_service_registry()


@pytest.mark.unit
def test_registry_register_resolve_exists_list() -> None:
    registry = ServiceRegistry()
    alpha = AlphaService()
    registry.register(alpha)
    assert registry.exists("alpha") is True
    assert registry.resolve("alpha") is alpha
    assert registry.list() == ("alpha",)


@pytest.mark.unit
def test_registry_duplicate_registration_raises() -> None:
    registry = ServiceRegistry()
    registry.register(AlphaService())
    with pytest.raises(ServiceRegistrationError):
        registry.register(AlphaService())


@pytest.mark.unit
def test_registry_unregister_and_missing() -> None:
    registry = ServiceRegistry()
    registry.register(AlphaService())
    registry.unregister("alpha")
    assert registry.exists("alpha") is False
    with pytest.raises(ServiceNotFoundError):
        registry.resolve("alpha")
    with pytest.raises(ServiceNotFoundError):
        registry.unregister("alpha")


@pytest.mark.unit
def test_registry_validate_dependency_order() -> None:
    registry = ServiceRegistry()
    alpha = AlphaService()
    beta = BetaService(alpha)
    registry.register(beta)
    registry.register(alpha)
    validation = registry.validate()
    assert validation.valid is True
    assert validation.startup_order == ("alpha", "beta")
    assert validation.shutdown_order == ("beta", "alpha")


@pytest.mark.unit
def test_registry_validate_missing_dependency() -> None:
    registry = ServiceRegistry()
    registry.register(BetaService(AlphaService()))
    validation = registry.validate()
    assert validation.valid is False
    assert any("Missing dependency" in error for error in validation.errors)


@pytest.mark.unit
def test_registry_validate_cycle_raises() -> None:
    registry = ServiceRegistry()

    class _CycleA(AlphaService):
        def name(self) -> str:
            return "cycle-a"

        def dependencies(self) -> tuple[str, ...]:
            return ("cycle-b",)

    class _CycleB(AlphaService):
        def name(self) -> str:
            return "cycle-b"

        def dependencies(self) -> tuple[str, ...]:
            return ("cycle-a",)

    registry.register(_CycleA())
    registry.register(_CycleB())
    with pytest.raises(CircularDependencyError):
        registry.validate()


@pytest.mark.unit
def test_get_service_registry_singleton() -> None:
    first = get_service_registry()
    second = get_service_registry()
    assert first is second
