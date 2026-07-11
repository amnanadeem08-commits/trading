"""RSI + MACD statistical candidate rule."""

from __future__ import annotations

from collections.abc import Sequence

from models.decision import DecisionSource, DecisionState
from signal_engine.candidates.candidate import DirectionCandidate
from signal_engine.exceptions import SignalRuleError
from signal_engine.indicators.technical import (
    IndicatorComputationError,
    compute_macd,
    compute_rsi,
    compute_sma,
)
from signal_engine.intake.market_intake import MarketIntakeFrame
from signal_engine.rules.base import CandidateRule


def closes_from_frames(frames: Sequence[MarketIntakeFrame]) -> tuple[float, ...]:
    """Extract close prices from market intake frames in order."""
    closes: list[float] = []
    for frame in frames:
        close = frame.ohlcv.get("close")
        if close is None:
            raise SignalRuleError(f"Frame {frame.frame_id} missing ohlcv.close")
        closes.append(float(close))
    return tuple(closes)


class RSIMACDRule(CandidateRule):
    """Generate BUY/SELL/HOLD candidates from RSI and MACD histogram."""

    def __init__(
        self,
        *,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        sma_period: int = 20,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ) -> None:
        if oversold >= overbought:
            raise SignalRuleError("oversold must be < overbought")
        self._rsi_period = rsi_period
        self._macd_fast = macd_fast
        self._macd_slow = macd_slow
        self._macd_signal = macd_signal
        self._sma_period = sma_period
        self._oversold = oversold
        self._overbought = overbought

    def evaluate(self, frames: Sequence[MarketIntakeFrame]) -> DirectionCandidate:
        if not frames:
            raise SignalRuleError("frames must not be empty")
        try:
            closes = closes_from_frames(frames)
            rsi = compute_rsi(closes, self._rsi_period)
            macd = compute_macd(
                closes,
                fast=self._macd_fast,
                slow=self._macd_slow,
                signal=self._macd_signal,
            )
            sma = compute_sma(closes, self._sma_period)
        except IndicatorComputationError as error:
            raise SignalRuleError(str(error)) from error

        rsi_name = f"rsi_{self._rsi_period}"
        sma_name = f"sma_{self._sma_period}"
        indicators_used = (
            rsi_name,
            "macd",
            "macd_signal",
            "macd_histogram",
            sma_name,
        )
        indicator_values: dict[str, float | str | int | bool] = {
            rsi_name: round(rsi, 6),
            "macd": round(macd.macd, 6),
            "macd_signal": round(macd.signal, 6),
            "macd_histogram": round(macd.histogram, 6),
            sma_name: round(sma, 6),
            "last_close": round(closes[-1], 6),
        }

        decision = DecisionState.HOLD
        confidence = 0.45
        rationale = "RSI and MACD are neutral; defaulting to HOLD."

        if rsi < self._oversold and macd.histogram > 0.0:
            decision = DecisionState.BUY
            confidence = min(
                0.95, 0.55 + ((self._oversold - rsi) / 100.0) + min(abs(macd.histogram), 1.0) * 0.2
            )
            rationale = (
                f"RSI {rsi:.2f} below oversold {self._oversold} with positive MACD histogram."
            )
        elif rsi > self._overbought and macd.histogram < 0.0:
            decision = DecisionState.SELL
            confidence = min(
                0.95,
                0.55 + ((rsi - self._overbought) / 100.0) + min(abs(macd.histogram), 1.0) * 0.2,
            )
            rationale = (
                f"RSI {rsi:.2f} above overbought {self._overbought} with negative MACD histogram."
            )

        return DirectionCandidate(
            decision=decision,
            decision_source=DecisionSource.STATISTICAL_ONLY,
            confidence=confidence,
            indicators_used=indicators_used,
            indicator_values=indicator_values,
            rationale=rationale,
        )
