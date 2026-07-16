"""Thread-safe in-memory strategy registry."""

from __future__ import annotations

from threading import RLock

from strategy_builder.contracts import StrategyDefinition
from strategy_builder.exceptions import (
    StrategyNotFoundError,
    StrategyRegistrationError,
)
from strategy_builder.identity import validate_strategy_identity


class StrategyRegistry:
    """Store unique strategy versions and explicit enablement state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._strategies: dict[tuple[str, str], StrategyDefinition] = {}

    def register(self, strategy: StrategyDefinition) -> None:
        """Register one immutable strategy/version pair."""
        validate_strategy_identity(strategy)
        key = (strategy.strategy_id, strategy.version)
        with self._lock:
            if key in self._strategies:
                raise StrategyRegistrationError(
                    "Strategy version already registered: "
                    f"{strategy.strategy_id}@{strategy.version}"
                )
            self._strategies[key] = strategy

    def resolve(self, strategy_id: str, version: str) -> StrategyDefinition:
        """Resolve a registered strategy version."""
        key = (strategy_id, version)
        with self._lock:
            strategy = self._strategies.get(key)
        if strategy is None:
            raise StrategyNotFoundError(strategy_id, version)
        return strategy

    def set_enabled(self, strategy_id: str, version: str, *, enabled: bool) -> StrategyDefinition:
        """Update only mutable enablement state without changing identity."""
        key = (strategy_id, version)
        with self._lock:
            strategy = self._strategies.get(key)
            if strategy is None:
                raise StrategyNotFoundError(strategy_id, version)
            updated = strategy.model_copy(update={"enabled": enabled})
            validate_strategy_identity(updated)
            self._strategies[key] = updated
            return updated

    def enable(self, strategy_id: str, version: str) -> StrategyDefinition:
        """Enable a registered strategy."""
        return self.set_enabled(strategy_id, version, enabled=True)

    def disable(self, strategy_id: str, version: str) -> StrategyDefinition:
        """Disable a registered strategy."""
        return self.set_enabled(strategy_id, version, enabled=False)

    def list(self, *, enabled_only: bool = False) -> tuple[StrategyDefinition, ...]:
        """List strategies in stable identity/version order."""
        with self._lock:
            strategies = tuple(self._strategies.values())
        selected = (
            tuple(strategy for strategy in strategies if strategy.enabled)
            if enabled_only
            else strategies
        )
        return tuple(sorted(selected, key=lambda item: (item.strategy_id, item.version)))
