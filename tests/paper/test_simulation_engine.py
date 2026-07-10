"""Unit tests for simulation engine."""

from __future__ import annotations

from datetime import UTC, datetime

from connectors import PaperState, SimulationClock, SimulationEngine, SimulationIdGenerator
from connectors.simulation.simulation_engine import SimulationOutcome
from tests.paper_helpers import make_paper_settings


def test_simulation_id_generator_deterministic() -> None:
    generator = SimulationIdGenerator(deterministic=True, seed=99)
    assert generator.next_execution_id() == "sim-99-000001"
    assert generator.next_execution_id() == "sim-99-000002"
    generator.reset()
    assert generator.next_execution_id() == "sim-99-000001"


def test_simulation_id_generator_random() -> None:
    generator = SimulationIdGenerator(deterministic=False)
    first = generator.next_execution_id()
    second = generator.next_execution_id()
    assert first.startswith("sim-")
    assert second.startswith("sim-")
    assert first != second


def test_simulation_clock_now_and_advance() -> None:
    clock = SimulationClock()
    started = clock.now()
    completed = clock.advance(base=started, milliseconds=0)
    assert completed == started
    advanced = clock.advance(base=started, milliseconds=10)
    assert advanced > started


def test_simulation_clock_advance_naive_datetime() -> None:
    clock = SimulationClock()
    naive = datetime(2026, 1, 1, 12, 0, 0)
    advanced = clock.advance(base=naive, milliseconds=5)
    assert advanced.tzinfo == UTC


def test_simulation_engine_generates_execution_id() -> None:
    engine = SimulationEngine(make_paper_settings(deterministic=True, random_seed=3))
    assert engine.generate_execution_id() == "sim-3-000001"


def test_simulation_engine_simulate_success() -> None:
    engine = SimulationEngine(
        make_paper_settings(failure_rate=0.0, latency_ms_min=2, latency_ms_max=2)
    )
    result = engine.simulate(request_id="req-1", execution_id="exec-1")
    assert result.execution_id == "exec-1"
    assert result.request_id == "req-1"
    assert result.status == PaperState.COMPLETED
    assert result.latency_ms == 2
    assert result.validation_passed is True
    assert result.synthetic_fill["filled"] is True


def test_simulation_engine_simulate_failure() -> None:
    engine = SimulationEngine(make_paper_settings(failure_rate=1.0))
    result = engine.simulate(request_id="req-2")
    assert result.status == PaperState.FAILED
    assert result.synthetic_fill["filled"] is False


def test_simulation_engine_simulate_outcome() -> None:
    engine = SimulationEngine(make_paper_settings())
    outcome = engine.simulate_outcome(request_id="req-3", execution_id="exec-3")
    assert isinstance(outcome, SimulationOutcome)
    assert outcome.execution_id == "exec-3"
    assert outcome.metadata["mode"] == "simulation"


def test_simulation_engine_reset() -> None:
    engine = SimulationEngine(make_paper_settings(deterministic=True, random_seed=11))
    first = engine.generate_execution_id()
    engine.reset()
    second = engine.generate_execution_id()
    assert first == second


def test_simulation_engine_equal_latency_bounds() -> None:
    engine = SimulationEngine(make_paper_settings(latency_ms_min=7, latency_ms_max=7))
    result = engine.simulate(request_id="req-4")
    assert result.latency_ms == 7


def test_simulation_engine_delay_disabled_by_default() -> None:
    engine = SimulationEngine(
        make_paper_settings(simulate_delay=False, latency_ms_min=100, latency_ms_max=100)
    )
    result = engine.simulate(request_id="req-5")
    assert result.latency_ms == 100
