"""Execution adapter registry."""

from __future__ import annotations

from threading import RLock

from connectors.adapters.adapter_metadata import AdapterMetadata, AdapterState
from connectors.adapters.execution_adapter import ExecutionAdapter
from connectors.exceptions import AdapterNotFoundError, AdapterRegistrationError

_default_adapter_registry: AdapterRegistry | None = None
_registry_lock = RLock()


class AdapterRegistry:
    """Thread-safe registry for execution adapter definitions and lifecycle state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._adapters: dict[str, AdapterMetadata] = {}
        self._types: dict[str, type[ExecutionAdapter]] = {}
        self._states: dict[str, AdapterState] = {}
        self._versions: dict[str, str] = {}

    def register(self, metadata: AdapterMetadata) -> None:
        """Register an adapter definition."""
        adapter_id = metadata.adapter_id
        if not adapter_id.strip():
            msg = "Adapter id must not be empty"
            raise AdapterRegistrationError(msg)
        with self._lock:
            if adapter_id in self._adapters:
                msg = f"Adapter already registered: {adapter_id}"
                raise AdapterRegistrationError(msg)
            self._adapters[adapter_id] = metadata
            self._states[adapter_id] = AdapterState.REGISTERED
            self._versions[adapter_id] = metadata.version

    def unregister(self, adapter_id: str) -> None:
        with self._lock:
            if adapter_id not in self._adapters:
                raise AdapterNotFoundError(adapter_id)
            del self._adapters[adapter_id]
            self._states.pop(adapter_id, None)
            self._types.pop(adapter_id, None)
            self._versions.pop(adapter_id, None)

    def register_type(self, adapter_type: type[ExecutionAdapter]) -> None:
        """Register an adapter implementation type."""
        instance = adapter_type()
        adapter_id = instance.adapter_id()
        with self._lock:
            self._types[adapter_id] = adapter_type
            if adapter_id not in self._adapters:
                metadata = instance.metadata()
                self._adapters[adapter_id] = metadata
                self._states[adapter_id] = AdapterState.REGISTERED
                self._versions[adapter_id] = metadata.version

    def resolve(self, adapter_id: str) -> AdapterMetadata:
        with self._lock:
            metadata = self._adapters.get(adapter_id)
        if metadata is None:
            raise AdapterNotFoundError(adapter_id)
        return metadata

    def resolve_type(self, adapter_id: str) -> type[ExecutionAdapter]:
        with self._lock:
            adapter_type = self._types.get(adapter_id)
        if adapter_type is None:
            raise AdapterNotFoundError(adapter_id)
        return adapter_type

    def get_state(self, adapter_id: str) -> AdapterState:
        with self._lock:
            state = self._states.get(adapter_id)
        if state is None:
            raise AdapterNotFoundError(adapter_id)
        return state

    def set_state(self, adapter_id: str, state: AdapterState) -> None:
        if not self.exists(adapter_id):
            raise AdapterNotFoundError(adapter_id)
        with self._lock:
            self._states[adapter_id] = state

    def get_version(self, adapter_id: str) -> str:
        with self._lock:
            version = self._versions.get(adapter_id)
        if version is None:
            raise AdapterNotFoundError(adapter_id)
        return version

    def exists(self, adapter_id: str) -> bool:
        with self._lock:
            return adapter_id in self._adapters

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._adapters.keys()))

    def list_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._types.keys()))


def get_adapter_registry() -> AdapterRegistry:
    """Return the process-wide default adapter registry."""
    global _default_adapter_registry
    with _registry_lock:
        if _default_adapter_registry is None:
            _default_adapter_registry = AdapterRegistry()
        return _default_adapter_registry


def reset_adapter_registry() -> None:
    """Reset the default adapter registry. Intended for tests."""
    global _default_adapter_registry
    with _registry_lock:
        _default_adapter_registry = None
