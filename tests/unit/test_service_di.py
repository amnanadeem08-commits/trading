"""Unit tests for dependency injection."""

from __future__ import annotations

import pytest

from services import (
    BaseService,
    ServiceContainer,
    ServiceResolutionError,
    build_application_context,
    build_service_factory,
    reset_application_context,
)
from tests.services_fixtures import AlphaService, BetaService


@pytest.fixture(autouse=True)
def _reset_context() -> None:
    reset_application_context()
    yield
    reset_application_context()


@pytest.mark.unit
def test_container_constructor_injection() -> None:
    container = ServiceContainer()
    container.register_instance(AlphaService, AlphaService())
    beta = container.resolve(BetaService)
    assert beta.name() == "beta"
    assert beta.ready() is False


@pytest.mark.unit
def test_container_singleton_resolution() -> None:
    container = ServiceContainer()
    first = container.resolve(AlphaService)
    second = container.resolve(AlphaService)
    assert first is second


@pytest.mark.unit
def test_container_missing_dependency_raises() -> None:
    class _CustomDependency:
        pass

    class _NeedsCustom(BaseService):
        def __init__(self, dependency: _CustomDependency) -> None:
            self._dependency = dependency

        def name(self) -> str:
            return "needs-custom"

        def version(self) -> str:
            return "1.0.0"

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

        def health(self):
            return AlphaService().health()

        def status(self):
            return AlphaService().status()

        def metrics(self) -> dict[str, object]:
            return {}

        def dependencies(self) -> tuple[str, ...]:
            return ()

        def ready(self) -> bool:
            return True

    container = ServiceContainer()
    with pytest.raises(ServiceResolutionError):
        container.resolve(_NeedsCustom)


@pytest.mark.unit
def test_service_factory_create_and_register() -> None:
    context = build_application_context()
    factory = build_service_factory(context)
    factory.register_type(AlphaService)
    factory.register_type(BetaService)
    alpha = factory.create(AlphaService)
    beta = factory.create(BetaService)
    assert factory.registry.exists("alpha") is True
    assert factory.registry.exists("beta") is True
    assert alpha.name() == "alpha"
    assert beta.name() == "beta"
    assert "alpha" in context.health.list_components()


@pytest.mark.unit
def test_service_factory_create_from_instance() -> None:
    factory = build_service_factory()
    service = factory.create_from_instance(AlphaService())
    assert factory.registry.resolve("alpha") is service
