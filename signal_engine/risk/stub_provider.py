"""Stub risk binding provider for tests and local wiring."""

from __future__ import annotations

from models.decision import DecisionState
from models.risk import RiskAssessment
from models.signal import InvalidationRule
from risk.scoring.confidence_score import ConfidenceScore
from signal_engine.exceptions import SignalRiskAttachmentError
from signal_engine.risk.risk_mapper import (
    build_invalidation_rule,
    build_risk_assessment,
    invalidation_from_atr,
    invalidation_from_structure,
)


class StubRiskBindingProvider:
    """Deterministic risk/confidence/invalidation provider (no live risk engine)."""

    def __init__(
        self,
        *,
        confidence: float = 0.62,
        fail: bool = False,
        zero_directional_confidence: bool = False,
    ) -> None:
        self._confidence = confidence
        self._fail = fail
        self._zero_directional_confidence = zero_directional_confidence

    def get_confidence(
        self,
        *,
        symbol_id: str,
        decision: DecisionState,
        indicator_values: dict[str, float | str | int | bool],
    ) -> ConfidenceScore:
        if self._fail:
            raise SignalRiskAttachmentError(f"stub risk provider forced failure for {symbol_id}")
        value = self._confidence
        if self._zero_directional_confidence and decision in {
            DecisionState.BUY,
            DecisionState.SELL,
        }:
            value = 0.0
        return ConfidenceScore(
            value=value,
            source="stub-risk",
            metadata={"symbol_id": symbol_id},
        )

    def get_assessment(
        self,
        *,
        symbol_id: str,
        decision: DecisionState,
        confidence: float,
        indicator_values: dict[str, float | str | int | bool],
    ) -> RiskAssessment:
        _ = indicator_values
        return build_risk_assessment(
            exposure_impact=(
                f"Stub exposure check for {symbol_id} "
                f"({decision.value}, confidence={confidence:.2f})."
            ),
            margin_impact="No margin pressure in stub mode.",
            notes="Confidence is not a probability of profit.",
        )

    def get_invalidation(
        self,
        *,
        decision: DecisionState,
        indicator_values: dict[str, float | str | int | bool],
    ) -> InvalidationRule:
        support = _optional_float(indicator_values.get("support"))
        resistance = _optional_float(indicator_values.get("resistance"))
        atr = _optional_float(indicator_values.get("atr_14"))
        price = _optional_float(indicator_values.get("close"))
        if support is not None or resistance is not None:
            try:
                return invalidation_from_structure(
                    decision,
                    support=support,
                    resistance=resistance,
                )
            except SignalRiskAttachmentError:
                pass
        if atr is not None and price is not None:
            return invalidation_from_atr(
                decision,
                current_price=price,
                atr=atr,
            )
        return build_invalidation_rule(
            condition="Stub invalidation: thesis fails if key levels break.",
        )


def _optional_float(value: float | str | int | bool | None) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except TypeError, ValueError:
        return None
