"""Contract tests for mandatory platform contracts."""

from __future__ import annotations

import pytest

from models import ExplainableSignal, ReproducibilityKey
from models.decision import DecisionSource, DecisionState
from models.events import DomainEvent, EventType, PredictionCreatedEvent
from models.prediction import LLMInsight, MLPrediction


def _reproducibility() -> ReproducibilityKey:
    return ReproducibilityKey(
        feature_snapshot_version="fs-1",
        model_version="ml-1",
        prompt_version="prompt-1",
        strategy_version="strategy-1",
        schema_version="1.0.0",
        config_hash="hash-1",
    )


@pytest.mark.contract
def test_explainable_signal_contract_has_all_required_fields() -> None:
    """Rule R7: every recommendation must be explainable."""
    required_fields = {
        "signal_id",
        "symbol_id",
        "market_id",
        "decision",
        "decision_source",
        "indicators_used",
        "indicator_values",
        "confidence",
        "risk_assessment",
        "invalidation",
        "alternative_scenario",
        "provenance",
        "reproducibility",
    }
    assert required_fields.issubset(set(ExplainableSignal.model_fields.keys()))


@pytest.mark.contract
def test_decision_state_has_seven_states() -> None:
    """Decision Engine must support all mandated states."""
    assert len(DecisionState) == 7


@pytest.mark.contract
def test_fail_safe_hold_source_exists() -> None:
    """Rule R18: fail-safe cascade must have explicit source."""
    assert DecisionSource.FAIL_SAFE_HOLD.value == "fail_safe_hold"


@pytest.mark.contract
def test_domain_event_is_versioned_and_traceable() -> None:
    """Rule R13/R14: events must be typed, versioned, traceable."""
    event = DomainEvent(
        event_type=EventType.PREDICTION_CREATED,
        market_id="crypto:binance",
        symbol_id="BTC/USDT",
        payload={"example": True},
    )
    assert event.event_id
    assert event.correlation_id
    assert event.event_version == "1.0.0"


@pytest.mark.contract
def test_prediction_created_event_carries_reproducibility() -> None:
    """Rule R14/R15: predictions must be reproducible and auditable."""
    event = PredictionCreatedEvent(
        market_id="crypto:binance",
        symbol_id="BTC/USDT",
        signal_id="sig-1",
        decision=DecisionState.HOLD,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        confidence=0.4,
        reproducibility=_reproducibility(),
    )
    assert event.reproducibility.config_hash == "hash-1"


@pytest.mark.contract
def test_ml_prediction_required_fields_for_ai_pipeline() -> None:
    """Rule R5: ML prediction is a first-class contract before AI."""
    required = {
        "direction",
        "direction_probabilities",
        "ml_confidence",
        "model_name",
        "model_version",
        "features_used",
    }
    assert required.issubset(set(MLPrediction.model_fields.keys()))


@pytest.mark.contract
def test_llm_insight_contract_fields() -> None:
    """Rule R7: LLM reasoning must include alternative scenario."""
    required = {
        "reasoning",
        "alternative_scenario",
        "fomo_fear_note",
        "provider",
        "model_name",
        "prompt_version",
    }
    assert required.issubset(set(LLMInsight.model_fields.keys()))


@pytest.mark.contract
def test_audit_record_fields_defined() -> None:
    """Rule R15: audit contract fields exist on AuditRecord model."""
    from models.events import AuditRecord
    from models.risk import RiskVerdictStatus

    record = AuditRecord(
        event_id="evt-1",
        market_id="crypto:binance",
        symbol_id="BTC/USDT",
        connector_version="0.0.0",
        strategy_version="1.0.0",
        model_version="ml-1",
        prompt_version="prompt-1",
        feature_snapshot_version="fs-1",
        confidence=0.5,
        decision=DecisionState.HOLD,
        risk_verdict=RiskVerdictStatus.APPROVED,
        reproducibility=_reproducibility(),
        feature_flags_active={"signal_only": True},
    )
    assert record.audit_id
    assert record.timestamp is not None
