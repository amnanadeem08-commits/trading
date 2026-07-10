"""Additional unit tests for services package coverage."""

from __future__ import annotations

import pytest

from config.settings import ServiceSettings
from services import (
    LifecycleManager,
    ServiceContainer,
    ServiceDiscovery,
    ServiceFactory,
    ServiceLifecycleError,
    ServiceNotFoundError,
    ServiceNotReadyError,
    ServiceProvider,
    ServiceRegistrationError,
    ServiceRegistry,
    ServiceResolutionError,
    build_application_context,
    build_service_factory,
    ensure_concrete_service,
    reset_application_context,
    reset_service_registry,
    service_metadata,
)
from services.exceptions import CircularDependencyError, ServiceError
from services.service import BaseService
from services.validation import ValidationResult
from tests.services_fixtures import AlphaService


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_service_registry()
    yield
    reset_application_context()
    reset_service_registry()


@pytest.mark.unit
def test_service_exceptions_expose_codes() -> None:
    assert ServiceNotFoundError("x").code == "service_not_found"
    assert ServiceRegistrationError("x").code == "service_registration_error"
    assert ServiceLifecycleError("x").code == "service_lifecycle_error"
    assert ServiceResolutionError("x").code == "service_resolution_error"
    assert ServiceNotReadyError("x").code == "service_not_ready"
    assert ServiceError("x").code == "service_error"


@pytest.mark.unit
def test_container_register_factory_and_clear() -> None:
    container = ServiceContainer()
    container.register_factory(AlphaService, AlphaService, singleton=False)
    first = container.resolve(AlphaService)
    second = container.resolve(AlphaService)
    assert first is not second
    assert AlphaService in container.registered_types()
    container.clear()
    assert container.registered_types() == ()


@pytest.mark.unit
def test_container_unknown_type_raises() -> None:
    container = ServiceContainer()

    class _NotAService:
        pass

    with pytest.raises(ServiceResolutionError):
        container.resolve(_NotAService)  # type: ignore[arg-type]


@pytest.mark.unit
def test_container_missing_required_parameter_raises() -> None:
    class _NeedsArg(BaseService):
        def __init__(self, required: str) -> None:
            self._required = required

        def name(self) -> str:
            return "needs-arg"

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
        container.resolve(_NeedsArg)


@pytest.mark.unit
def test_registry_empty_name_raises() -> None:
    registry = ServiceRegistry()

    class _EmptyName(AlphaService):
        def name(self) -> str:
            return "   "

    with pytest.raises(ServiceRegistrationError):
        registry.register(_EmptyName())


@pytest.mark.unit
def test_provider_properties_and_lifecycle_emit() -> None:
    context = build_application_context()
    registry = ServiceRegistry()
    container = ServiceContainer()
    lifecycle = LifecycleManager(registry, context, context.settings.services)
    provider = ServiceProvider(container, registry, context, lifecycle)
    assert provider.container is container
    assert provider.registry is registry
    assert provider.context is context
    provider.wire(AlphaService())
    assert lifecycle.events[-1].event_type.value == "service_registered"


@pytest.mark.unit
def test_factory_register_custom_factory() -> None:
    context = build_application_context()
    factory: ServiceFactory = build_service_factory(context)
    factory.register_type(AlphaService, factory=lambda: AlphaService(), singleton=True)
    service = factory.create(AlphaService)
    assert service.name() == "alpha"


@pytest.mark.unit
def test_lifecycle_off_event_unsubscribe() -> None:
    context = build_application_context()
    registry = ServiceRegistry()
    lifecycle = LifecycleManager(registry, context, context.settings.services)
    seen: list[str] = []
    subscription = lifecycle.on_event(lambda event: seen.append(event.event_type.value))
    lifecycle.off_event(subscription)
    lifecycle.emit_registered(AlphaService())
    assert seen == []


@pytest.mark.unit
def test_lifecycle_shutdown_failure_non_graceful() -> None:
    context = build_application_context()
    non_graceful_settings = ServiceSettings(graceful_shutdown=False)
    updated_settings = context.settings.model_copy(update={"services": non_graceful_settings})
    context = build_application_context(settings=updated_settings)
    registry = ServiceRegistry()
    alpha = AlphaService()
    registry.register(alpha)
    lifecycle = LifecycleManager(registry, context, context.settings.services)
    lifecycle.startup()
    alpha._tracker.fail_stop = True
    result = lifecycle.shutdown()
    assert result.success is False


@pytest.mark.unit
def test_lifecycle_shutdown_skips_inactive_service() -> None:
    context = build_application_context()
    registry = ServiceRegistry()
    registry.register(AlphaService())
    lifecycle = LifecycleManager(registry, context, context.settings.services)
    result = lifecycle.shutdown()
    assert result.success is True
    assert result.operations[0].message == "already stopped"


@pytest.mark.unit
def test_discovery_ensure_concrete_service_rejects_abstract() -> None:
    with pytest.raises(ServiceRegistrationError):
        ensure_concrete_service(BaseService)


@pytest.mark.unit
def test_discovery_module_without_path() -> None:
    discovery = ServiceDiscovery(package_name="services.exceptions")
    discovered = discovery.discover()
    assert discovered == ()


@pytest.mark.unit
def test_validation_result_model() -> None:
    result = ValidationResult(valid=True, startup_order=("a",), shutdown_order=("a",))
    assert result.errors == ()


@pytest.mark.unit
def test_validate_self_dependency() -> None:
    registry = ServiceRegistry()

    class _SelfDep(AlphaService):
        def name(self) -> str:
            return "self-dep"

        def dependencies(self) -> tuple[str, ...]:
            return ("self-dep",)

    registry.register(_SelfDep())
    validation = registry.validate()
    assert validation.valid is False
    assert any("depends on itself" in error for error in validation.errors)


@pytest.mark.unit
def test_decorator_without_metadata_defaults() -> None:
    class _Plain(AlphaService):
        pass

    metadata = service_metadata(_Plain)
    assert metadata["auto_register"] is False


@pytest.mark.unit
def test_discovery_register_discovered_from_services_package() -> None:
    registry = ServiceRegistry()
    discovery = ServiceDiscovery(package_name="services")
    registered = discovery.register_discovered(registry, modules=("services",))
    assert registered == ()


@pytest.mark.unit
def test_lifecycle_startup_not_ready_raises_failed() -> None:
    context = build_application_context()
    registry = ServiceRegistry()

    class _NeverReady(AlphaService):
        def name(self) -> str:
            return "never-ready"

        def start(self) -> None:
            self._tracker.state = __import__(
                "services.service",
                fromlist=["ServiceState"],
            ).ServiceState.RUNNING

        def ready(self) -> bool:
            return False

    registry.register(_NeverReady())
    lifecycle = LifecycleManager(registry, context, context.settings.services)
    result = lifecycle.startup()
    assert result.success is False


@pytest.mark.unit
def test_circular_dependency_error_exposes_cycle() -> None:
    error = CircularDependencyError(("a", "b", "a"))
    assert error.cycle == ("a", "b", "a")
