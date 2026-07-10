"""Simulation identifier generation."""

from __future__ import annotations

from uuid import uuid4


class SimulationIdGenerator:
    """Generates synthetic execution identifiers."""

    def __init__(self, *, deterministic: bool = False, seed: int = 42) -> None:
        self._deterministic = deterministic
        self._seed = seed
        self._counter = 0

    def next_execution_id(self, *, prefix: str = "sim") -> str:
        """Return the next synthetic execution identifier."""
        if self._deterministic:
            self._counter += 1
            return f"{prefix}-{self._seed}-{self._counter:06d}"
        return f"{prefix}-{uuid4()}"

    def reset(self) -> None:
        """Reset the deterministic counter."""
        self._counter = 0
