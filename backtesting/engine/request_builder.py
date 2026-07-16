"""Helpers to build signal assembly requests for backtests."""

from __future__ import annotations

from models.common import ReproducibilityKey
from models.decision import DecisionSource, DecisionState
from models.risk import RiskAssessment
from models.signal import InvalidationRule, Provenance
from signal_engine.contracts.assembly_request import SignalAssemblyRequest


def make_backtest_assembly_request(**overrides: object) -> SignalAssemblyRequest:
    payload: dict[str, object] = {
        "signal_id": "sig-bt-0",
        "symbol_id": "BTC/USDT",
        "market_id": "crypto:binance",
        "decision": DecisionState.HOLD,
        "decision_source": DecisionSource.STATISTICAL_ONLY,
        "indicators_used": ("rsi_14",),
        "indicator_values": {"rsi_14": 55.0},
        "confidence": 0.5,
        "risk_assessment": RiskAssessment(exposure_impact="Within backtest position limits."),
        "invalidation": InvalidationRule(condition="Break below support"),
        "alternative_scenario": "Breakout would shift bias.",
        "provenance": Provenance(
            market_id="crypto:binance",
            connector_version="backtest-0.0.0",
            prompt_version="prompt-bt-1",
            strategy_version="1.0.0",
            feature_snapshot_version="fs-bt-0",
        ),
        "reproducibility": ReproducibilityKey(
            feature_snapshot_version="fs-bt-0",
            model_version="none",
            prompt_version="prompt-bt-1",
            strategy_version="1.0.0",
            schema_version="1.0.0",
            config_hash="backtest",
        ),
        "ml_prediction": None,
        "llm_insight": None,
    }
    payload.update(overrides)
    return SignalAssemblyRequest.model_validate(payload)
