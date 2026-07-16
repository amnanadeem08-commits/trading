"""Signal evaluation adapter for backtest replay."""

from __future__ import annotations

from collections.abc import Sequence

from backtesting.engine.request_builder import make_backtest_assembly_request
from market_data.models.candle import Candle
from models.common import ReproducibilityKey
from models.decision import DecisionSource, DecisionState
from models.signal import ExplainableSignal, InvalidationRule
from signal_engine import (
    RSIMACDRule,
    SignalAssembler,
    SignalRuleError,
    StubRiskBindingProvider,
    apply_candidate,
    attach_risk_bindings_from_provider,
    market_intake_from_candle,
    provenance_from_intake,
)
from signal_engine.intake.feature_intake import FeatureIntakePayload


def evaluate_signal_at_bar(
    candles: Sequence[Candle],
    *,
    market_id: str,
    bar_index: int,
    strategy_version: str,
    config_hash: str,
) -> ExplainableSignal | None:
    """Evaluate the statistical signal rule using only the provided candle window."""
    if not candles:
        return None
    frames = tuple(market_intake_from_candle(candle, market_id=market_id) for candle in candles)
    try:
        candidate = RSIMACDRule().evaluate(frames)
    except SignalRuleError:
        return None
    if candidate.decision not in {DecisionState.BUY, DecisionState.SELL}:
        return None

    last = candles[-1]
    close = float(last.close)
    indicator_values = {
        **dict(candidate.indicator_values),
        "close": close,
        "support": close * 0.98,
        "atr_14": max(close * 0.01, 0.01),
    }
    feature = FeatureIntakePayload(
        payload_id=f"bt-fs-{bar_index}",
        symbol_id=last.symbol_id,
        dataset_id=last.dataset_id,
        indicators_used=candidate.indicators_used,
        indicator_values=indicator_values,
        source_vector_id=f"bt-vector-{bar_index}",
        version=f"fs-bt-{bar_index}",
    )
    provenance = provenance_from_intake(
        market=frames[-1],
        features=feature,
        connector_version="backtest-0.0.0",
        strategy_version=strategy_version,
        prompt_version="prompt-bt-1",
    )
    reproducibility = ReproducibilityKey(
        feature_snapshot_version=feature.version,
        model_version="none",
        prompt_version="prompt-bt-1",
        strategy_version=strategy_version,
        schema_version="1.0.0",
        config_hash=config_hash,
    )
    request = make_backtest_assembly_request(
        signal_id=f"sig-bt-{bar_index}",
        symbol_id=last.symbol_id,
        market_id=market_id,
        provenance=provenance,
        reproducibility=reproducibility,
        indicator_values=indicator_values,
        indicators_used=candidate.indicators_used,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        ml_prediction=None,
        llm_insight=None,
    )
    request = apply_candidate(request, candidate)
    request = attach_risk_bindings_from_provider(request, StubRiskBindingProvider())
    support = float(indicator_values["support"])
    request = request.model_copy(
        update={
            "invalidation": InvalidationRule(
                condition="Break below support invalidates directional bias.",
                price_level=support,
            )
        }
    )
    return SignalAssembler().assemble(request)
