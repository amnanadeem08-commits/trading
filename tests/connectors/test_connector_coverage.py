"""Coverage tests for connector framework edge cases."""

from __future__ import annotations

import pytest

from connectors import (
    AdapterRegistry,
    ConnectorFrameworkRegistry,
)
from connectors.exceptions import (
    AdapterNotFoundError,
    AdapterRegistrationError,
    AdapterStateError,
    ConnectorOrchestrationError,
    ConnectorValidationError,
    DispatchBridgeError,
)
from tests.connectors_helpers import make_adapter_metadata


def test_exception_types() -> None:
    assert AdapterNotFoundError("id").adapter_id == "id"
    assert AdapterStateError("id", "registered", "shutdown").operation == "shutdown"
    assert isinstance(DispatchBridgeError("bad"), Exception)
    assert isinstance(ConnectorValidationError("bad"), Exception)
    assert isinstance(ConnectorOrchestrationError("bad"), Exception)


def test_connector_registry_empty_id_raises() -> None:
    from connectors.registry.connector_registry import ConnectorRecord

    adapters = AdapterRegistry()
    adapters.register(make_adapter_metadata())
    registry = ConnectorFrameworkRegistry(adapter_registry=adapters)
    with pytest.raises(AdapterRegistrationError):
        registry.register(
            ConnectorRecord(
                connector_id="   ",
                adapter_id="sample-adapter",
                name="Sample",
                version="1.0.0",
            )
        )


def test_connector_registry_unregistered_adapter_raises() -> None:
    from connectors.registry.connector_registry import ConnectorRecord

    registry = ConnectorFrameworkRegistry()
    with pytest.raises(AdapterNotFoundError):
        registry.register(
            ConnectorRecord(
                connector_id="conn-1",
                adapter_id="missing",
                name="Sample",
                version="1.0.0",
            )
        )


def test_adapter_registry_empty_id_raises() -> None:
    registry = AdapterRegistry()
    with pytest.raises(AdapterRegistrationError):
        registry.register(make_adapter_metadata(adapter_id="   "))


def test_connector_registry_unregister() -> None:
    from connectors.registry.connector_registry import ConnectorRecord

    adapters = AdapterRegistry()
    adapters.register(make_adapter_metadata())
    registry = ConnectorFrameworkRegistry(adapter_registry=adapters)
    registry.register(
        ConnectorRecord(
            connector_id="conn-1",
            adapter_id="sample-adapter",
            name="Sample",
            version="1.0.0",
        )
    )
    registry.unregister("conn-1")
    with pytest.raises(AdapterNotFoundError):
        registry.resolve("conn-1")


def test_connector_registry_state_not_found() -> None:
    registry = ConnectorFrameworkRegistry()
    with pytest.raises(AdapterNotFoundError):
        registry.get_state("missing")


def test_adapter_registry_version_not_found() -> None:
    registry = AdapterRegistry()
    with pytest.raises(AdapterNotFoundError):
        registry.get_version("missing")
