"""Agent registry."""

from __future__ import annotations

from threading import RLock

from ai.agents.agent import Agent, AgentMetadata
from ai.agents.agent_lifecycle import AgentState
from ai.exceptions import AgentNotFoundError, AgentRegistrationError

_default_agent_registry: AgentRegistry | None = None
_registry_lock = RLock()


class AgentRegistry:
    """Thread-safe registry for AI agent definitions and implementations."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._agents: dict[str, AgentMetadata] = {}
        self._types: dict[str, type[Agent]] = {}
        self._states: dict[str, AgentState] = {}

    def register(self, metadata: AgentMetadata) -> None:
        """Register an agent definition."""
        agent_id = metadata.agent_id
        if not agent_id.strip():
            msg = "Agent id must not be empty"
            raise AgentRegistrationError(msg)
        with self._lock:
            if agent_id in self._agents:
                msg = f"Agent already registered: {agent_id}"
                raise AgentRegistrationError(msg)
            self._agents[agent_id] = metadata
            self._states[agent_id] = AgentState.CREATED

    def unregister(self, agent_id: str) -> None:
        with self._lock:
            if agent_id not in self._agents:
                raise AgentNotFoundError(agent_id)
            del self._agents[agent_id]
            self._states.pop(agent_id, None)
            self._types.pop(agent_id, None)

    def register_type(self, agent_type: type[Agent]) -> None:
        """Register an agent implementation type."""
        instance = agent_type()
        agent_id = instance.agent_id()
        with self._lock:
            self._types[agent_id] = agent_type
            if agent_id not in self._agents:
                self._agents[agent_id] = instance.metadata()
                self._states[agent_id] = AgentState.CREATED

    def resolve(self, agent_id: str) -> AgentMetadata:
        with self._lock:
            metadata = self._agents.get(agent_id)
        if metadata is None:
            raise AgentNotFoundError(agent_id)
        return metadata

    def resolve_type(self, agent_id: str) -> type[Agent]:
        with self._lock:
            agent_type = self._types.get(agent_id)
        if agent_type is None:
            raise AgentNotFoundError(agent_id)
        return agent_type

    def get_state(self, agent_id: str) -> AgentState:
        with self._lock:
            state = self._states.get(agent_id)
        if state is None:
            raise AgentNotFoundError(agent_id)
        return state

    def set_state(self, agent_id: str, state: AgentState) -> None:
        if not self.exists(agent_id):
            raise AgentNotFoundError(agent_id)
        with self._lock:
            self._states[agent_id] = state

    def exists(self, agent_id: str) -> bool:
        with self._lock:
            return agent_id in self._agents

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._agents.keys()))

    def list_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._types.keys()))


def get_agent_registry() -> AgentRegistry:
    """Return the process-wide default agent registry."""
    global _default_agent_registry
    with _registry_lock:
        if _default_agent_registry is None:
            _default_agent_registry = AgentRegistry()
        return _default_agent_registry


def reset_agent_registry() -> None:
    """Reset the default agent registry. Intended for tests."""
    global _default_agent_registry
    with _registry_lock:
        _default_agent_registry = None
