"""Shared builders for signal_engine tests."""

from __future__ import annotations

from models.common import ReproducibilityKey, VersionInfo
from models.decision import DecisionSource, DecisionState
from models.prediction import LLMInsight, MLPrediction, SignalDirection
from models.risk import RiskAssessment
from models.signal import InvalidationRule, Provenance
from signal_engine import SignalAssemblyRequest


def make_reproducibility() -> ReproducibilityKey:
    return ReproducibilityKey(
        feature_snapshot_version="fs-1",
        model_version="ml-1",
        prompt_version="prompt-1",
        strategy_version="strategy-1",
        schema_version="1.0.0",
        config_hash="abc123",
    )


def make_ml_prediction() -> MLPrediction:
    return MLPrediction(
        direction=SignalDirection.BUY,
        direction_probabilities={"BUY": 0.7, "SELL": 0.1, "HOLD": 0.2},
        ml_confidence=0.7,
        model_name="baseline",
        model_version=VersionInfo(version_id="ml-1"),
        features_used=("rsi_14", "macd"),
    )


def make_llm_insight() -> LLMInsight:
    return LLMInsight(
        reasoning="Momentum supports a cautious long bias.",
        alternative_scenario="A breakdown below support would invalidate the long thesis.",
        fomo_fear_note="Market context is neutral.",
        provider="anthropic",
        model_name="claude-sonnet-4-6",
        prompt_version=VersionInfo(version_id="prompt-1"),
    )


def make_risk_assessment() -> RiskAssessment:
    return RiskAssessment(
        exposure_impact="Within position limits.",
        margin_impact="No margin pressure.",
    )


def make_assembly_request(**overrides: object) -> SignalAssemblyRequest:
    payload: dict[str, object] = {
        "signal_id": "sig-1",
        "symbol_id": "BTC/USDT",
        "market_id": "crypto:binance",
        "decision": DecisionState.HOLD,
        "decision_source": DecisionSource.STATISTICAL_ONLY,
        "indicators_used": ("rsi_14",),
        "indicator_values": {"rsi_14": 55.0},
        "confidence": 0.5,
        "risk_assessment": make_risk_assessment(),
        "invalidation": InvalidationRule(condition="Break below support"),
        "alternative_scenario": "Breakout would shift bias to BUY.",
        "provenance": Provenance(
            market_id="crypto:binance",
            connector_version="0.0.0",
            prompt_version="prompt-1",
            strategy_version="1.0.0",
            feature_snapshot_version="fs-1",
        ),
        "reproducibility": make_reproducibility(),
        "ml_prediction": None,
        "llm_insight": None,
    }
    payload.update(overrides)
    return SignalAssemblyRequest.model_validate(payload)
