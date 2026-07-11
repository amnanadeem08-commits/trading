"""Unit tests for paper_trading skeleton and orchestration API."""

from __future__ import annotations

import pytest

from config.settings import AppSettings, get_settings, reset_settings
from connectors.adapters.paper import PaperExecutionAdapter
from models.decision import DecisionState
from paper_trading import (
    PaperLiveTradingDisabledError,
    PaperOrchestrationRequest,
    PaperRegistrationError,
    PaperSessionNotFoundError,
    PaperSessionRegistry,
    PaperSessionStatus,
    PaperTradingOrchestrator,
    get_paper_registry,
    reset_paper_registry,
)
from signal_engine import SignalAssembler
from tests.signal_helpers import make_assembly_request


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_paper_registry()
    reset_settings()
    yield
    reset_paper_registry()
    reset_settings()


def _signal():
    return SignalAssembler().assemble(make_assembly_request(signal_id="sig-paper-1"))


@pytest.mark.unit
def test_paper_trading_settings_load_from_yaml() -> None:
    settings = AppSettings.from_sources()
    assert settings.paper_trading.registry_enabled is True
    assert settings.paper_trading.max_sessions == 10_000
    assert settings.paper_trading.orchestration_enabled is True
    assert settings.paper_trading.refuse_when_live_trading_enabled is True
    assert settings.paper_trading.risk_gate_required_before_fill is True
    assert settings.feature_flags.live_trading_enabled is False


@pytest.mark.unit
def test_public_api_and_prepare_registers_session() -> None:
    orchestrator = PaperTradingOrchestrator()
    assert orchestrator.paper_adapter is None
    result = orchestrator.prepare_from_signal(_signal(), session_id="ps-1")
    assert result.status == PaperSessionStatus.PREPARED
    assert result.signal_id == "sig-paper-1"
    assert result.decision in {
        DecisionState.BUY,
        DecisionState.SELL,
        DecisionState.HOLD,
    }
    record = orchestrator.get_session("ps-1")
    assert record.session_id == "ps-1"
    assert get_paper_registry().size == 1


@pytest.mark.unit
def test_orchestrator_accepts_injected_paper_adapter_without_fill() -> None:
    adapter = PaperExecutionAdapter()
    orchestrator = PaperTradingOrchestrator(paper_adapter=adapter)
    assert orchestrator.paper_adapter is adapter
    result = orchestrator.prepare(PaperOrchestrationRequest(session_id="ps-2", signal=_signal()))
    assert result.status == PaperSessionStatus.PREPARED


@pytest.mark.unit
def test_refuses_when_live_trading_enabled() -> None:
    settings = get_settings()
    live = settings.model_copy(
        update={
            "feature_flags": settings.feature_flags.model_copy(
                update={"live_trading_enabled": True}
            )
        }
    )
    orchestrator = PaperTradingOrchestrator(settings=live)
    with pytest.raises(PaperLiveTradingDisabledError):
        orchestrator.prepare_from_signal(_signal(), session_id="ps-live")


@pytest.mark.unit
def test_registry_capacity_and_missing() -> None:
    registry = PaperSessionRegistry(max_sessions=1)
    orchestrator = PaperTradingOrchestrator(registry=registry)
    orchestrator.prepare_from_signal(_signal(), session_id="ps-a")
    with pytest.raises(PaperRegistrationError, match="capacity"):
        orchestrator.prepare_from_signal(
            SignalAssembler().assemble(make_assembly_request(signal_id="sig-2")),
            session_id="ps-b",
        )
    with pytest.raises(PaperSessionNotFoundError):
        registry.get("missing")
    with pytest.raises(PaperRegistrationError, match="max_sessions"):
        PaperSessionRegistry(max_sessions=0)
