"""Policy registry."""

from __future__ import annotations

from threading import RLock

from decision.exceptions import PolicyNotFoundError, PolicyRegistrationError
from decision.policy.decision_policy import DecisionPolicy, PolicyMetadata

_default_policy_registry: PolicyRegistry | None = None
_registry_lock = RLock()


class PolicyRegistry:
    """Thread-safe registry for decision policy definitions and implementations."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._policies: dict[str, PolicyMetadata] = {}
        self._types: dict[str, type[DecisionPolicy]] = {}

    def register(self, metadata: PolicyMetadata) -> None:
        """Register a policy definition."""
        policy_id = metadata.policy_id
        if not policy_id.strip():
            msg = "Policy id must not be empty"
            raise PolicyRegistrationError(msg)
        with self._lock:
            if policy_id in self._policies:
                msg = f"Policy already registered: {policy_id}"
                raise PolicyRegistrationError(msg)
            self._policies[policy_id] = metadata

    def unregister(self, policy_id: str) -> None:
        with self._lock:
            if policy_id not in self._policies:
                raise PolicyNotFoundError(policy_id)
            del self._policies[policy_id]
            self._types.pop(policy_id, None)

    def register_type(self, policy_type: type[DecisionPolicy]) -> None:
        """Register a policy implementation type."""
        instance = policy_type()
        policy_id = instance.policy_id()
        with self._lock:
            self._types[policy_id] = policy_type
            if policy_id not in self._policies:
                self._policies[policy_id] = instance.metadata()

    def resolve(self, policy_id: str) -> PolicyMetadata:
        with self._lock:
            metadata = self._policies.get(policy_id)
        if metadata is None:
            raise PolicyNotFoundError(policy_id)
        return metadata

    def resolve_type(self, policy_id: str) -> type[DecisionPolicy]:
        with self._lock:
            policy_type = self._types.get(policy_id)
        if policy_type is None:
            raise PolicyNotFoundError(policy_id)
        return policy_type

    def exists(self, policy_id: str) -> bool:
        with self._lock:
            return policy_id in self._policies

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._policies.keys()))

    def list_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._types.keys()))


def get_policy_registry() -> PolicyRegistry:
    """Return the process-wide default policy registry."""
    global _default_policy_registry
    with _registry_lock:
        if _default_policy_registry is None:
            _default_policy_registry = PolicyRegistry()
        return _default_policy_registry


def reset_policy_registry() -> None:
    """Reset the default policy registry. Intended for tests."""
    global _default_policy_registry
    with _registry_lock:
        _default_policy_registry = None
