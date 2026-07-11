"""E2E integration: intake → rules → ML/LLM/risk → assemble → validate → event."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from audit import AuditLogger, InMemoryAuditStore
from config.settings import get_settings, reset_settings
from events import EventBus, EventType, InMemoryEventPersistenceStore, reset_event_bus
from market_data.models.candle import Candle
from models.decision import DecisionSource, DecisionState
from models.events import PredictionCreatedEvent
from models.signal import ExplainableSignal
from signal_engine import (
    RSIMACDRule,
    SignalAssembler,
    SignalLifecycleService,
    SignalRegistry,
    SignalValidationError,
    StubLLMInsightProvider,
    StubMLPredictionProvider,
    StubRiskBindingProvider,
    apply_candidate,
    attach_llm_insight_from_provider,
    attach_ml_prediction_from_provider,
    attach_risk_bindings_from_provider,
    market_intake_from_candle,
    provenance_from_intake,
    reset_signal_registry,
)
from signal_engine.intake.feature_intake import FeatureIntakePayload
from tests.signal_helpers import make_assembly_request


@pytest.fixture(autouse=True)
def _reset_globals() -> None:
    reset_event_bus()
    reset_signal_registry()
    reset_settings()
    yield
    reset_event_bus()
    reset_signal_registry()
    reset_settings()


def _candles(closes: list[float]) -> tuple[Candle, ...]:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    candles: list[Candle] = []
    for index, close in enumerate(closes):
        candles.append(
            Candle(
                record_id=f"c-{index}",
                dataset_id="crypto:binance",
                symbol_id="BTC/USDT",
                timestamp=start + timedelta(hours=index),
                open=close,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=10.0,
                sequence=index,
            )
        )
    return tuple(candles)


def _build_ai_enhanced_request():
    closes = [float(100 + index) for index in range(50)]
    frames = tuple(
        market_intake_from_candle(candle, market_id="crypto:binance") for candle in _candles(closes)
    )
    candidate = RSIMACDRule().evaluate(frames)
    indicator_values = {
        **dict(candidate.indicator_values),
        "close": float(closes[-1]),
        "support": float(closes[-1]) - 5.0,
        "atr_14": 1.5,
    }
    feature = FeatureIntakePayload(
        payload_id="e2e-fs-1",
        symbol_id="BTC/USDT",
        dataset_id="crypto:binance",
        indicators_used=candidate.indicators_used,
        indicator_values=indicator_values,
        source_vector_id="e2e-vector-1",
        version="fs-e2e-1",
    )
    provenance = provenance_from_intake(
        market=frames[-1],
        features=feature,
        connector_version="e2e-0.0.0",
        strategy_version="e2e-1.0.0",
        prompt_version="prompt-e2e-1",
    )
    request = make_assembly_request(
        signal_id="sig-e2e-1",
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        provenance=provenance,
        indicator_values=indicator_values,
        indicators_used=candidate.indicators_used,
    )
    request = apply_candidate(request, candidate)
    request = attach_ml_prediction_from_provider(
        request,
        StubMLPredictionProvider(),
        decision_source=DecisionSource.ML_ONLY,
    )
    request = attach_llm_insight_from_provider(request, StubLLMInsightProvider())
    request = attach_risk_bindings_from_provider(request, StubRiskBindingProvider())
    return request


@pytest.mark.integration
def test_signal_engine_e2e_intake_to_event() -> None:
    settings = get_settings()
    assert settings.feature_flags.live_trading_enabled is False
    assert settings.feature_flags.signal_only is True

    store = InMemoryEventPersistenceStore()
    bus = EventBus(persistence=store)
    audit_store = InMemoryAuditStore()
    registry = SignalRegistry()
    lifecycle = SignalLifecycleService(
        registry=registry,
        event_bus=bus,
        audit_logger=AuditLogger(audit_store),
    )

    request = _build_ai_enhanced_request()
    assert request.decision_source == DecisionSource.AI_ENHANCED_ML
    assert request.ml_prediction is not None
    assert request.llm_insight is not None
    assert request.confidence > 0
    assert request.risk_assessment.exposure_impact.strip()
    assert request.invalidation.condition.strip()

    record = lifecycle.assemble_and_register(request)
    assert record.signal_id == "sig-e2e-1"
    assert registry.get("sig-e2e-1").signal.llm_insight is not None
    assert store.count() >= 1
    created = next(
        event for event in store.list_events() if event.event_type == EventType.PREDICTION_CREATED
    )
    assert isinstance(created, PredictionCreatedEvent)
    assert created.signal_id == "sig-e2e-1"
    assert created.payload.get("lifecycle_state") == "accepted"
    audits = audit_store.read(event_id=created.event_id)
    assert len(audits) == 1
    assert audits[0].decision == created.decision


@pytest.mark.integration
def test_signal_engine_e2e_reject_path_is_explicit() -> None:
    store = InMemoryEventPersistenceStore()
    bus = EventBus(persistence=store)
    registry = SignalRegistry()
    lifecycle = SignalLifecycleService(registry=registry, event_bus=bus)

    request = _build_ai_enhanced_request()
    signal = SignalAssembler().assemble(request)
    broken = ExplainableSignal.model_construct(
        signal_id=signal.signal_id,
        symbol_id=signal.symbol_id,
        market_id=signal.market_id,
        decision=DecisionState.BUY,
        decision_source=signal.decision_source,
        indicators_used=signal.indicators_used,
        indicator_values=signal.indicator_values,
        ml_prediction=signal.ml_prediction,
        llm_insight=signal.llm_insight,
        confidence=0.0,
        risk_assessment=signal.risk_assessment,
        invalidation=signal.invalidation,
        alternative_scenario=signal.alternative_scenario,
        provenance=signal.provenance,
        reproducibility=signal.reproducibility,
    )

    with pytest.raises(SignalValidationError, match="rejected") as err:
        lifecycle.register_signal(broken)

    assert err.value.reasons
    assert registry.size == 0
    assert any(
        event.event_type == EventType.VALIDATION_COMPLETED and event.payload.get("passed") is False
        for event in store.list_events()
    )
