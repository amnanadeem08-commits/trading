"""Connector framework registry."""

from __future__ import annotations

from threading import RLock

from pydantic import Field

from connectors.adapters.adapter_metadata import AdapterState
from connectors.adapters.adapter_registry import AdapterRegistry
from connectors.exceptions import AdapterNotFoundError, AdapterRegistrationError
from models.common import PlatformModel

_default_connector_registry: ConnectorRegistry | None = None
_registry_lock = RLock()


class ConnectorRecord(PlatformModel):
    """Framework-level connector registration record."""

    connector_id: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""


class ConnectorRegistry:
    """Thread-safe registry for connector framework definitions."""

    def __init__(self, *, adapter_registry: AdapterRegistry | None = None) -> None:
        self._lock = RLock()
        self._adapters = adapter_registry or AdapterRegistry()
        self._connectors: dict[str, ConnectorRecord] = {}
        self._states: dict[str, AdapterState] = {}

    @property
    def adapters(self) -> AdapterRegistry:
        """Return the underlying adapter registry."""
        return self._adapters

    def register(self, record: ConnectorRecord) -> None:
        """Register a connector definition linked to an adapter."""
        connector_id = record.connector_id
        if not connector_id.strip():
            msg = "Connector id must not be empty"
            raise AdapterRegistrationError(msg)
        if not self._adapters.exists(record.adapter_id):
            raise AdapterNotFoundError(record.adapter_id)
        with self._lock:
            if connector_id in self._connectors:
                msg = f"Connector already registered: {connector_id}"
                raise AdapterRegistrationError(msg)
            self._connectors[connector_id] = record
            self._states[connector_id] = AdapterState.REGISTERED

    def unregister(self, connector_id: str) -> None:
        with self._lock:
            if connector_id not in self._connectors:
                raise AdapterNotFoundError(connector_id)
            del self._connectors[connector_id]
            self._states.pop(connector_id, None)

    def resolve(self, connector_id: str) -> ConnectorRecord:
        with self._lock:
            record = self._connectors.get(connector_id)
        if record is None:
            raise AdapterNotFoundError(connector_id)
        return record

    def get_state(self, connector_id: str) -> AdapterState:
        with self._lock:
            state = self._states.get(connector_id)
        if state is None:
            raise AdapterNotFoundError(connector_id)
        return state

    def set_state(self, connector_id: str, state: AdapterState) -> None:
        with self._lock:
            if connector_id not in self._connectors:
                raise AdapterNotFoundError(connector_id)
            self._states[connector_id] = state

    def exists(self, connector_id: str) -> bool:
        with self._lock:
            return connector_id in self._connectors

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._connectors.keys()))


def get_connector_framework_registry() -> ConnectorRegistry:
    """Return the process-wide default connector framework registry."""
    global _default_connector_registry
    with _registry_lock:
        if _default_connector_registry is None:
            _default_connector_registry = ConnectorRegistry()
        return _default_connector_registry


def reset_connector_framework_registry() -> None:
    """Reset the default connector framework registry. Intended for tests."""
    global _default_connector_registry
    with _registry_lock:
        _default_connector_registry = None
