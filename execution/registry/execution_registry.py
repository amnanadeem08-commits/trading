"""Execution engine registry."""

from __future__ import annotations

from threading import RLock

from execution.engine.execution_engine import ExecutionEngine, ExecutionEngineMetadata
from execution.engine.execution_state import ExecutionState
from execution.exceptions import ExecutionNotFoundError, ExecutionRegistrationError

_default_execution_registry: ExecutionRegistry | None = None
_registry_lock = RLock()


class ExecutionRegistry:
    """Thread-safe registry for execution engine definitions and lifecycle state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._engines: dict[str, ExecutionEngineMetadata] = {}
        self._types: dict[str, type[ExecutionEngine]] = {}
        self._engine_states: dict[str, ExecutionState] = {}
        self._execution_states: dict[str, ExecutionState] = {}
        self._execution_engines: dict[str, str] = {}
        self._versions: dict[str, str] = {}

    def register(self, metadata: ExecutionEngineMetadata) -> None:
        """Register an execution engine definition."""
        engine_id = metadata.engine_id
        if not engine_id.strip():
            msg = "Engine id must not be empty"
            raise ExecutionRegistrationError(msg)
        with self._lock:
            if engine_id in self._engines:
                msg = f"Execution engine already registered: {engine_id}"
                raise ExecutionRegistrationError(msg)
            self._engines[engine_id] = metadata
            self._engine_states[engine_id] = ExecutionState.CREATED
            self._versions[engine_id] = metadata.version

    def unregister(self, engine_id: str) -> None:
        with self._lock:
            if engine_id not in self._engines:
                raise ExecutionNotFoundError(engine_id)
            del self._engines[engine_id]
            self._engine_states.pop(engine_id, None)
            self._types.pop(engine_id, None)
            self._versions.pop(engine_id, None)

    def register_type(self, engine_type: type[ExecutionEngine]) -> None:
        """Register an execution engine implementation type."""
        instance = engine_type()
        engine_id = instance.engine_id()
        with self._lock:
            self._types[engine_id] = engine_type
            if engine_id not in self._engines:
                metadata = instance.metadata()
                self._engines[engine_id] = metadata
                self._engine_states[engine_id] = ExecutionState.CREATED
                self._versions[engine_id] = metadata.version

    def resolve(self, engine_id: str) -> ExecutionEngineMetadata:
        with self._lock:
            metadata = self._engines.get(engine_id)
        if metadata is None:
            raise ExecutionNotFoundError(engine_id)
        return metadata

    def resolve_type(self, engine_id: str) -> type[ExecutionEngine]:
        with self._lock:
            engine_type = self._types.get(engine_id)
        if engine_type is None:
            raise ExecutionNotFoundError(engine_id)
        return engine_type

    def get_engine_state(self, engine_id: str) -> ExecutionState:
        with self._lock:
            state = self._engine_states.get(engine_id)
        if state is None:
            raise ExecutionNotFoundError(engine_id)
        return state

    def set_engine_state(self, engine_id: str, state: ExecutionState) -> None:
        if not self.exists(engine_id):
            raise ExecutionNotFoundError(engine_id)
        with self._lock:
            self._engine_states[engine_id] = state

    def track_execution(
        self,
        execution_id: str,
        *,
        engine_id: str,
        state: ExecutionState = ExecutionState.CREATED,
        version_id: str = "",
    ) -> None:
        """Record lifecycle state for an individual execution operation."""
        with self._lock:
            self._execution_states[execution_id] = state
            self._execution_engines[execution_id] = engine_id
            if version_id:
                self._versions[execution_id] = version_id

    def get_execution_state(self, execution_id: str) -> ExecutionState:
        with self._lock:
            state = self._execution_states.get(execution_id)
        if state is None:
            raise ExecutionNotFoundError(execution_id)
        return state

    def set_execution_state(self, execution_id: str, state: ExecutionState) -> None:
        with self._lock:
            if execution_id not in self._execution_states:
                raise ExecutionNotFoundError(execution_id)
            self._execution_states[execution_id] = state

    def get_version(self, identifier: str) -> str:
        with self._lock:
            version = self._versions.get(identifier)
        if version is None:
            raise ExecutionNotFoundError(identifier)
        return version

    def exists(self, engine_id: str) -> bool:
        with self._lock:
            return engine_id in self._engines

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._engines.keys()))

    def list_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._types.keys()))


def get_execution_registry() -> ExecutionRegistry:
    """Return the process-wide default execution registry."""
    global _default_execution_registry
    with _registry_lock:
        if _default_execution_registry is None:
            _default_execution_registry = ExecutionRegistry()
        return _default_execution_registry


def reset_execution_registry() -> None:
    """Reset the default execution registry. Intended for tests."""
    global _default_execution_registry
    with _registry_lock:
        _default_execution_registry = None
