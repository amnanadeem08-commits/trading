"""Narrow adapter from strategy evaluation to the Backtesting V1 signal boundary."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from backtesting.engine.request_builder import make_backtest_assembly_request
from market_data.models.candle import Candle
from models.common import ReproducibilityKey
from models.decision import DecisionSource, DecisionState
from models.signal import ExplainableSignal, InvalidationRule
from signal_engine.assembly.assembler import SignalAssembler
from signal_engine.candidates.candidate import DirectionCandidate
from signal_engine.intake.feature_intake import FeatureIntakePayload
from signal_engine.intake.market_intake import market_intake_from_candle
from signal_engine.intake.provenance import provenance_from_intake
from signal_engine.rules.apply import apply_candidate
from strategy_builder.contracts import (
    PositionContext,
    ProtectionKind,
    StrategyDefinition,
    StrategyEvaluationResult,
    StrategyOutcome,
)
from strategy_builder.evaluation import StrategyEvaluator


def candidate_from_evaluation(
    strategy: StrategyDefinition,
    result: StrategyEvaluationResult,
) -> DirectionCandidate | None:
    """Map actionable strategy outcomes into the existing statistical candidate."""
    decision = {
        StrategyOutcome.BUY: DecisionState.BUY,
        StrategyOutcome.SELL: DecisionState.SELL,
        StrategyOutcome.EXIT: DecisionState.FULL_EXIT,
    }.get(result.outcome)
    if decision is None or not result.valid:
        return None
    values: dict[str, float | str | int | bool] = dict(result.indicator_values)
    values["triggered_rule_ids"] = ",".join(result.triggered_rule_ids)
    return DirectionCandidate(
        decision=decision,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        confidence=1.0,
        indicators_used=tuple(spec.indicator_id for spec in strategy.required_indicators),
        indicator_values=values,
        rationale=result.explanation,
    )


def evaluate_strategy_candidate_at_bar(
    candles: Sequence[Candle],
    *,
    strategy: StrategyDefinition,
    market_id: str,
    timeframe: str,
    position: PositionContext | None = None,
) -> DirectionCandidate | None:
    """Evaluate only the supplied history window and return an actionable candidate."""
    result = StrategyEvaluator().evaluate(
        strategy,
        candles,
        market=market_id,
        timeframe=timeframe,
        position=position,
    )
    return candidate_from_evaluation(strategy, result)


def evaluate_strategy_signal_at_bar(
    candles: Sequence[Candle],
    *,
    strategy: StrategyDefinition,
    market_id: str,
    timeframe: str,
    bar_index: int,
    config_hash: str,
    position: PositionContext | None = None,
) -> ExplainableSignal | None:
    """Build the same ExplainableSignal contract consumed by Backtesting V1."""
    if not candles:
        return None
    candidate = evaluate_strategy_candidate_at_bar(
        candles,
        strategy=strategy,
        market_id=market_id,
        timeframe=timeframe,
        position=position,
    )
    if candidate is None:
        return None

    last = candles[-1]
    values = dict(candidate.indicator_values)
    close = float(last.close)
    values["close"] = close
    feature_version = f"strategy-{strategy.version_hash[:12]}-{bar_index}"
    feature = FeatureIntakePayload(
        payload_id=f"strategy-feature-{bar_index}",
        symbol_id=last.symbol_id,
        dataset_id=last.dataset_id,
        indicators_used=candidate.indicators_used,
        indicator_values=values,
        source_vector_id=f"strategy-vector-{bar_index}",
        version=feature_version,
    )
    market_frame = market_intake_from_candle(last, market_id=market_id)
    provenance = provenance_from_intake(
        market=market_frame,
        features=feature,
        connector_version="backtest-strategy-1.0.0",
        strategy_version=strategy.version,
        prompt_version="none",
    )
    reproducibility = ReproducibilityKey(
        feature_snapshot_version=feature.version,
        model_version="none",
        prompt_version="none",
        strategy_version=strategy.version,
        schema_version=strategy.schema_version,
        config_hash=config_hash,
    )
    signal_digest = hashlib.sha256(
        (
            f"{strategy.version_hash}|{last.symbol_id}|{last.timestamp.isoformat()}|"
            f"{bar_index}|{candidate.decision.value}"
        ).encode()
    ).hexdigest()[:20]
    request = make_backtest_assembly_request(
        signal_id=f"sig-strategy-{signal_digest}",
        symbol_id=last.symbol_id,
        market_id=market_id,
        provenance=provenance,
        reproducibility=reproducibility,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        indicators_used=candidate.indicators_used,
        indicator_values=values,
        ml_prediction=None,
        llm_insight=None,
    )
    request = apply_candidate(request, candidate)
    request = request.model_copy(
        update={
            "invalidation": _invalidation(strategy, candidate.decision, close),
            "alternative_scenario": candidate.rationale,
        }
    )
    return SignalAssembler().assemble(request)


def _invalidation(
    strategy: StrategyDefinition,
    decision: DecisionState,
    close: float,
) -> InvalidationRule:
    stop = strategy.stop_loss_rule
    level: float | None = None
    if stop.kind == ProtectionKind.PERCENTAGE:
        if decision == DecisionState.BUY:
            level = close * (1.0 - stop.value)
        elif decision == DecisionState.SELL:
            level = close * (1.0 + stop.value)
    return InvalidationRule(
        condition=(
            f"Strategy {strategy.strategy_id}@{strategy.version} stop-loss rule invalidates "
            "the directional entry."
        ),
        price_level=level,
    )
