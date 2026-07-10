"""Decision engine registry."""

from __future__ import annotations

from threading import RLock

from decision.engine.decision_engine import DecisionEngine, DecisionEngineMetadata
from decision.engine.decision_state import DecisionState
from decision.exceptions import DecisionNotFoundError, DecisionRegistrationError

_default_decision_registry: DecisionRegistry | None = None
_registry_lock = RLock()


class DecisionRegistry:
    """Thread-safe registry for decision engine definitions and implementations."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._engines: dict[str, DecisionEngineMetadata] = {}
        self._types: dict[str, type[DecisionEngine]] = {}
        self._states: dict[str, DecisionState] = {}

    def register(self, metadata: DecisionEngineMetadata) -> None:
        """Register a decision engine definition."""
        engine_id = metadata.engine_id
        if not engine_id.strip():
            msg = "Engine id must not be empty"
            raise DecisionRegistrationError(msg)
        with self._lock:
            if engine_id in self._engines:
                msg = f"Decision engine already registered: {engine_id}"
                raise DecisionRegistrationError(msg)
            self._engines[engine_id] = metadata
            self._states[engine_id] = DecisionState.CREATED

    def unregister(self, engine_id: str) -> None:
        with self._lock:
            if engine_id not in self._engines:
                raise DecisionNotFoundError(engine_id)
            del self._engines[engine_id]
            self._states.pop(engine_id, None)
            self._types.pop(engine_id, None)

    def register_type(self, engine_type: type[DecisionEngine]) -> None:
        """Register a decision engine implementation type."""
        instance = engine_type()
        engine_id = instance.engine_id()
        with self._lock:
            self._types[engine_id] = engine_type
            if engine_id not in self._engines:
                self._engines[engine_id] = instance.metadata()
                self._states[engine_id] = DecisionState.CREATED

    def resolve(self, engine_id: str) -> DecisionEngineMetadata:
        with self._lock:
            metadata = self._engines.get(engine_id)
        if metadata is None:
            raise DecisionNotFoundError(engine_id)
        return metadata

    def resolve_type(self, engine_id: str) -> type[DecisionEngine]:
        with self._lock:
            engine_type = self._types.get(engine_id)
        if engine_type is None:
            raise DecisionNotFoundError(engine_id)
        return engine_type

    def get_state(self, engine_id: str) -> DecisionState:
        with self._lock:
            state = self._states.get(engine_id)
        if state is None:
            raise DecisionNotFoundError(engine_id)
        return state

    def set_state(self, engine_id: str, state: DecisionState) -> None:
        if not self.exists(engine_id):
            raise DecisionNotFoundError(engine_id)
        with self._lock:
            self._states[engine_id] = state

    def exists(self, engine_id: str) -> bool:
        with self._lock:
            return engine_id in self._engines

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._engines.keys()))

    def list_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._types.keys()))


def get_decision_registry() -> DecisionRegistry:
    """Return the process-wide default decision registry."""
    global _default_decision_registry
    with _registry_lock:
        if _default_decision_registry is None:
            _default_decision_registry = DecisionRegistry()
        return _default_decision_registry


def reset_decision_registry() -> None:
    """Reset the default decision registry. Intended for tests."""
    global _default_decision_registry
    with _registry_lock:
        _default_decision_registry = None
