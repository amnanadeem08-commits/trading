"""Offline simulation engine for paper execution."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from connectors.adapters.paper.paper_order_state import PaperState
from connectors.adapters.paper.paper_result import PaperExecutionResult
from connectors.adapters.paper.paper_settings import PaperSettings
from connectors.simulation.simulation_clock import SimulationClock
from connectors.simulation.simulation_id import SimulationIdGenerator


@dataclass(frozen=True)
class SimulationOutcome:
    """Raw outcome produced by the simulation engine."""

    execution_id: str
    success: bool
    latency_ms: int
    duration_ms: int
    status: PaperState
    metadata: dict[str, str]
    synthetic_fill: dict[str, object]


class SimulationEngine:
    """Generates deterministic offline simulation artifacts."""

    def __init__(
        self,
        settings: PaperSettings | None = None,
        *,
        clock: SimulationClock | None = None,
        id_generator: SimulationIdGenerator | None = None,
    ) -> None:
        self._settings = settings or PaperSettings()
        self._clock = clock or SimulationClock()
        self._id_generator = id_generator or SimulationIdGenerator(
            deterministic=self._settings.deterministic,
            seed=self._settings.random_seed,
        )
        self._rng = random.Random(self._settings.random_seed)

    @property
    def settings(self) -> PaperSettings:
        return self._settings

    def generate_execution_id(self) -> str:
        """Generate a synthetic execution identifier."""
        return self._id_generator.next_execution_id()

    def simulate(
        self,
        *,
        request_id: str,
        execution_id: str | None = None,
        historical_record: dict[str, object] | None = None,
    ) -> PaperExecutionResult:
        """Simulate a dispatch operation and return a paper execution result."""
        resolved_execution_id = execution_id or self.generate_execution_id()
        started_at = self._clock.now()
        latency_ms = self._sample_latency()
        duration_ms = self._sample_duration(latency_ms)

        if self._settings.simulate_delay and latency_ms > 0:
            time.sleep(latency_ms / 1000)

        success = self._rng.random() >= self._settings.failure_rate
        status = PaperState.COMPLETED if success else PaperState.FAILED
        completed_at = self._clock.advance(base=started_at, milliseconds=duration_ms)

        synthetic_fill: dict[str, object] = {
            "execution_id": resolved_execution_id,
            "request_id": request_id,
            "filled": success,
            "quantity": 1.0,
            "price": 100.0,
        }
        if historical_record is not None:
            for key, value in historical_record.items():
                if key not in {"execution_id", "request_id"}:
                    synthetic_fill[key] = value
        metadata = {
            "mode": "simulation",
            "deterministic": str(self._settings.deterministic).lower(),
            "seed": str(self._settings.random_seed),
        }
        if historical_record is not None:
            metadata["historical_replay"] = "true"

        return PaperExecutionResult(
            execution_id=resolved_execution_id,
            request_id=request_id,
            status=status,
            latency_ms=latency_ms,
            duration_ms=duration_ms,
            metadata=metadata,
            validation_passed=True,
            started_at=started_at,
            completed_at=completed_at,
            synthetic_fill=synthetic_fill,
        )

    def simulate_outcome(
        self,
        *,
        request_id: str,
        execution_id: str | None = None,
    ) -> SimulationOutcome:
        """Simulate and return a compact outcome structure."""
        result = self.simulate(request_id=request_id, execution_id=execution_id)
        return SimulationOutcome(
            execution_id=result.execution_id,
            success=result.status == PaperState.COMPLETED,
            latency_ms=result.latency_ms,
            duration_ms=result.duration_ms,
            status=result.status,
            metadata=dict(result.metadata),
            synthetic_fill=dict(result.synthetic_fill),
        )

    def reset(self) -> None:
        """Reset deterministic generators."""
        self._id_generator.reset()
        self._rng = random.Random(self._settings.random_seed)

    def _sample_latency(self) -> int:
        minimum = self._settings.latency_ms_min
        maximum = self._settings.latency_ms_max
        if minimum == maximum:
            return minimum
        return self._rng.randint(minimum, maximum)

    def _sample_duration(self, latency_ms: int) -> int:
        return latency_ms + self._rng.randint(0, max(1, latency_ms // 2))
