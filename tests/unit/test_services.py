"""Unit tests for services package."""

from __future__ import annotations

import pytest

from services import (
    ApplicationContext,
    ServiceDiscovery,
    ServiceRegistry,
    build_application_context,
    discover_service_types,
    reset_application_context,
    reset_service_registry,
    service_metadata,
    validate_services,
)
from tests.services_fixtures import AlphaService, GammaService


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_service_registry()
    yield
    reset_application_context()
    reset_service_registry()


@pytest.mark.unit
def test_application_context_exposes_required_dependencies() -> None:
    context = build_application_context()
    assert isinstance(context.settings.app_name, str)
    assert context.feature_flags is not None
    assert context.event_bus is not None
    assert context.metrics is not None
    assert context.health is not None
    assert context.audit is not None
    assert context.version_registry.services is not None
    assert context.logger_factory is not None
    assert len(context.configuration_hash) == 64


@pytest.mark.unit
def test_application_context_has_only_approved_surface() -> None:
    fields = set(ApplicationContext.__dataclass_fields__)
    assert fields == {
        "settings",
        "feature_flags",
        "event_bus",
        "metrics",
        "health",
        "audit",
        "version_registry",
        "logger_factory",
        "configuration_hash",
    }


@pytest.mark.unit
def test_validate_services_name_mismatch() -> None:
    class _Mismatch(AlphaService):
        def name(self) -> str:
            return "other"

    result = validate_services({"alpha": _Mismatch()})
    assert result.valid is False
    assert any("name mismatch" in error for error in result.errors)


@pytest.mark.unit
def test_service_metadata_from_decorator() -> None:
    metadata = service_metadata(GammaService)
    assert metadata["name"] == "gamma"
    assert metadata["auto_register"] is True


@pytest.mark.unit
def test_discovery_finds_fixture_services() -> None:
    discovered = discover_service_types(modules=("tests.services_fixtures",))
    names = {service_type.__name__ for service_type in discovered}
    assert "AlphaService" in names
    assert "BetaService" in names
    assert "GammaService" in names


@pytest.mark.unit
def test_discovery_register_discovered_only_auto_register() -> None:
    registry = ServiceRegistry()
    discovery = ServiceDiscovery()
    registered = discovery.register_discovered(registry, modules=("tests.services_fixtures",))
    assert registered == ("gamma",)
    assert registry.exists("gamma") is True
    assert registry.exists("alpha") is False
