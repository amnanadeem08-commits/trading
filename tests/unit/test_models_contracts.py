"""Unit tests for domain model contracts."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models.common import ReproducibilityKey, VersionInfo
from models.decision import DecisionSource, DecisionState, TradingDecision
from models.market import AssetClass, NormalizedBar, Symbol
from models.prediction import LLMInsight, MLPrediction, SignalDirection
from models.risk import RiskAssessment
from models.signal import ExplainableSignal, InvalidationRule, Provenance


def _version(version_id: str = "1.0.0") -> VersionInfo:
    return VersionInfo(version_id=version_id)


def _reproducibility() -> ReproducibilityKey:
    return ReproducibilityKey(
        feature_snapshot_version="fs-1",
        model_version="ml-1",
        prompt_version="prompt-1",
        strategy_version="strategy-1",
        schema_version="1.0.0",
        config_hash="abc123",
    )


def _ml_prediction() -> MLPrediction:
    return MLPrediction(
        direction=SignalDirection.BUY,
        direction_probabilities={"BUY": 0.7, "SELL": 0.1, "HOLD": 0.2},
        ml_confidence=0.7,
        model_name="baseline",
        model_version=_version("ml-1"),
        features_used=("rsi_14", "macd"),
    )


def _llm_insight() -> LLMInsight:
    return LLMInsight(
        reasoning="Momentum supports a cautious long bias.",
        alternative_scenario="A breakdown below support would invalidate the long thesis.",
        fomo_fear_note="Market context is neutral.",
        provider="anthropic",
        model_name="claude-sonnet-4-6",
        prompt_version=_version("prompt-1"),
    )


def _risk_assessment() -> RiskAssessment:
    return RiskAssessment(
        exposure_impact="Within position limits.",
        margin_impact="No margin pressure.",
    )


@pytest.mark.unit
def test_normalized_bar_rejects_high_below_low() -> None:
    with pytest.raises(ValidationError):
        NormalizedBar(
            timestamp=datetime.now(UTC),
            open=100.0,
            high=90.0,
            low=95.0,
            close=92.0,
            volume=1000.0,
            symbol_id="BTC/USDT",
            market_id="crypto:binance",
            timeframe="4h",
        )


@pytest.mark.unit
def test_symbol_contract_fields() -> None:
    symbol = Symbol(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        asset_class=AssetClass.CRYPTO,
        base_asset="BTC",
        quote_asset="USDT",
    )
    assert symbol.is_active is True
    assert symbol.asset_class == AssetClass.CRYPTO


@pytest.mark.unit
def test_reproducibility_key_rejects_empty_fields() -> None:
    with pytest.raises(ValidationError):
        ReproducibilityKey(
            feature_snapshot_version="",
            model_version="ml-1",
            prompt_version="prompt-1",
            strategy_version="strategy-1",
            schema_version="1.0.0",
            config_hash="abc123",
        )


@pytest.mark.unit
def test_trading_decision_is_immutable() -> None:
    decision = TradingDecision(
        decision_id="dec-1",
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        state=DecisionState.HOLD,
        source=DecisionSource.ML_ONLY,
        confidence=0.6,
        strategy_id="ai_strategy",
        strategy_version="1.0.0",
        reproducibility=_reproducibility(),
        rationale="No edge detected.",
    )
    with pytest.raises(ValidationError):
        decision.confidence = 0.9  # type: ignore[misc]


@pytest.mark.unit
def test_explainable_signal_requires_ml_for_ml_only_source() -> None:
    with pytest.raises(ValidationError):
        ExplainableSignal(
            signal_id="sig-1",
            symbol_id="BTC/USDT",
            market_id="crypto:binance",
            decision=DecisionState.HOLD,
            decision_source=DecisionSource.ML_ONLY,
            indicators_used=("rsi_14",),
            indicator_values={"rsi_14": 55.0},
            ml_prediction=None,
            confidence=0.5,
            risk_assessment=_risk_assessment(),
            invalidation=InvalidationRule(condition="Break below support"),
            alternative_scenario="Breakout would shift bias to BUY.",
            provenance=Provenance(
                market_id="crypto:binance",
                connector_version="0.0.0",
                prompt_version="prompt-1",
                strategy_version="1.0.0",
                feature_snapshot_version="fs-1",
            ),
            reproducibility=_reproducibility(),
        )


@pytest.mark.unit
def test_explainable_signal_valid_ai_enhanced_contract() -> None:
    signal = ExplainableSignal(
        signal_id="sig-1",
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        decision=DecisionState.BUY,
        decision_source=DecisionSource.AI_ENHANCED_ML,
        indicators_used=("rsi_14", "macd"),
        indicator_values={"rsi_14": 58.0, "macd": 0.12},
        ml_prediction=_ml_prediction(),
        llm_insight=_llm_insight(),
        confidence=0.72,
        risk_assessment=_risk_assessment(),
        invalidation=InvalidationRule(condition="Close below 95000", price_level=95000.0),
        alternative_scenario="Range continuation would favor HOLD.",
        provenance=Provenance(
            market_id="crypto:binance",
            connector_version="0.0.0",
            model_versions={"baseline": "ml-1"},
            prompt_version="prompt-1",
            strategy_version="1.0.0",
            provider="anthropic",
            feature_snapshot_version="fs-1",
        ),
        reproducibility=_reproducibility(),
    )
    assert signal.decision == DecisionState.BUY
    assert signal.ml_prediction is not None
    assert signal.llm_insight is not None
