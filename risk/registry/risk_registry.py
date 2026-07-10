"""Risk engine registry."""

from __future__ import annotations

from threading import RLock

from risk.engine.risk_engine import RiskEngine, RiskEngineMetadata
from risk.engine.risk_state import RiskState
from risk.exceptions import RiskNotFoundError, RiskRegistrationError

_default_risk_registry: RiskRegistry | None = None
_registry_lock = RLock()


class RiskRegistry:
    """Thread-safe registry for risk engine definitions and implementations."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._engines: dict[str, RiskEngineMetadata] = {}
        self._types: dict[str, type[RiskEngine]] = {}
        self._states: dict[str, RiskState] = {}

    def register(self, metadata: RiskEngineMetadata) -> None:
        """Register a risk engine definition."""
        engine_id = metadata.engine_id
        if not engine_id.strip():
            msg = "Engine id must not be empty"
            raise RiskRegistrationError(msg)
        with self._lock:
            if engine_id in self._engines:
                msg = f"Risk engine already registered: {engine_id}"
                raise RiskRegistrationError(msg)
            self._engines[engine_id] = metadata
            self._states[engine_id] = RiskState.CREATED

    def unregister(self, engine_id: str) -> None:
        with self._lock:
            if engine_id not in self._engines:
                raise RiskNotFoundError(engine_id)
            del self._engines[engine_id]
            self._states.pop(engine_id, None)
            self._types.pop(engine_id, None)

    def register_type(self, engine_type: type[RiskEngine]) -> None:
        """Register a risk engine implementation type."""
        instance = engine_type()
        engine_id = instance.engine_id()
        with self._lock:
            self._types[engine_id] = engine_type
            if engine_id not in self._engines:
                self._engines[engine_id] = instance.metadata()
                self._states[engine_id] = RiskState.CREATED

    def resolve(self, engine_id: str) -> RiskEngineMetadata:
        with self._lock:
            metadata = self._engines.get(engine_id)
        if metadata is None:
            raise RiskNotFoundError(engine_id)
        return metadata

    def resolve_type(self, engine_id: str) -> type[RiskEngine]:
        with self._lock:
            engine_type = self._types.get(engine_id)
        if engine_type is None:
            raise RiskNotFoundError(engine_id)
        return engine_type

    def get_state(self, engine_id: str) -> RiskState:
        with self._lock:
            state = self._states.get(engine_id)
        if state is None:
            raise RiskNotFoundError(engine_id)
        return state

    def set_state(self, engine_id: str, state: RiskState) -> None:
        if not self.exists(engine_id):
            raise RiskNotFoundError(engine_id)
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


def get_risk_registry() -> RiskRegistry:
    """Return the process-wide default risk registry."""
    global _default_risk_registry
    with _registry_lock:
        if _default_risk_registry is None:
            _default_risk_registry = RiskRegistry()
        return _default_risk_registry


def reset_risk_registry() -> None:
    """Reset the default risk registry. Intended for tests."""
    global _default_risk_registry
    with _registry_lock:
        _default_risk_registry = None
