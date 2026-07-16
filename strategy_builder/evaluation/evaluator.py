"""Deterministic, fail-closed strategy rule evaluator."""

from __future__ import annotations

import math
from collections.abc import Sequence

from market_data.models.candle import Candle
from strategy_builder.contracts import (
    ComparisonOperator,
    ComparisonRule,
    ConstantOperand,
    IndicatorOperand,
    PositionContext,
    RuleNode,
    RuleOperand,
    RuleTrace,
    StrategyDefinition,
    StrategyEvaluationResult,
    StrategyOutcome,
)
from strategy_builder.exceptions import StrategyBuilderError, StrategyValidationError
from strategy_builder.identity import validate_strategy_identity
from strategy_builder.indicators import evaluate_indicator, evaluate_indicators


def _rule_nodes(node: RuleNode) -> tuple[RuleNode, ...]:
    if isinstance(node, ComparisonRule):
        return (node,)
    return (node, *(item for child in node.children for item in _rule_nodes(child)))


def _crossing_indicator_ids(roots: Sequence[RuleNode]) -> frozenset[str]:
    identifiers: set[str] = set()
    for root in roots:
        for node in _rule_nodes(root):
            if not isinstance(node, ComparisonRule):
                continue
            if node.operator not in {
                ComparisonOperator.CROSSING_ABOVE,
                ComparisonOperator.CROSSING_BELOW,
            }:
                continue
            for operand in (node.left, node.right):
                if isinstance(operand, IndicatorOperand):
                    identifiers.add(operand.indicator_id)
    return frozenset(identifiers)


def _operand_value(operand: RuleOperand, values: dict[str, float]) -> float:
    if isinstance(operand, ConstantOperand):
        return operand.value
    try:
        return values[operand.indicator_id]
    except KeyError as error:
        raise StrategyValidationError(
            f"Missing evaluated indicator {operand.indicator_id}"
        ) from error


class StrategyEvaluator:
    """Evaluate a strategy against candles available through the current bar."""

    def evaluate(
        self,
        strategy: StrategyDefinition,
        candles: Sequence[Candle],
        *,
        market: str,
        timeframe: str,
        position: PositionContext | None = None,
    ) -> StrategyEvaluationResult:
        """Return an audited strategy outcome without raising data errors."""
        traces: list[RuleTrace] = []
        current_values: dict[str, float] = {}
        try:
            validate_strategy_identity(strategy)
            self._validate_context(strategy, candles, market=market, timeframe=timeframe)
            current_values = evaluate_indicators(strategy.required_indicators, candles)
            roots = (
                (strategy.exit_rules,)
                if position is not None
                else tuple(
                    node
                    for node in (strategy.entry_rules.buy, strategy.entry_rules.sell)
                    if node is not None
                )
            )
            crossing_ids = _crossing_indicator_ids(roots)
            previous_values = self._previous_values(strategy, candles, crossing_ids)

            if position is not None:
                matched = self._evaluate_node(
                    strategy.exit_rules,
                    current_values,
                    previous_values,
                    traces,
                )
                outcome = StrategyOutcome.EXIT if matched else StrategyOutcome.HOLD
                return self._result(
                    strategy,
                    outcome,
                    current_values,
                    traces,
                    (
                        "Exit rules matched."
                        if matched
                        else "Exit rules did not match; holding position."
                    ),
                )

            buy_matched = (
                self._evaluate_node(
                    strategy.entry_rules.buy,
                    current_values,
                    previous_values,
                    traces,
                )
                if strategy.entry_rules.buy is not None
                else False
            )
            sell_matched = (
                self._evaluate_node(
                    strategy.entry_rules.sell,
                    current_values,
                    previous_values,
                    traces,
                )
                if strategy.entry_rules.sell is not None
                else False
            )
            if buy_matched and sell_matched:
                return self._result(
                    strategy,
                    StrategyOutcome.HOLD,
                    current_values,
                    traces,
                    "Conflicting BUY and SELL entry rules matched; failed closed to HOLD.",
                    valid=False,
                )
            if buy_matched:
                return self._result(
                    strategy,
                    StrategyOutcome.BUY,
                    current_values,
                    traces,
                    "BUY entry rules matched.",
                )
            if sell_matched:
                return self._result(
                    strategy,
                    StrategyOutcome.SELL,
                    current_values,
                    traces,
                    "SELL entry rules matched.",
                )
            return self._result(
                strategy,
                StrategyOutcome.HOLD,
                current_values,
                traces,
                "No entry rules matched; defaulted to HOLD.",
            )
        except (StrategyBuilderError, TypeError, ValueError) as error:
            return StrategyEvaluationResult(
                strategy_id=strategy.strategy_id,
                strategy_version=strategy.version,
                outcome=StrategyOutcome.HOLD,
                explanation=f"Evaluation failed closed to HOLD: {error}",
                indicator_values=current_values,
                traces=tuple(traces),
                valid=False,
            )

    @staticmethod
    def _validate_context(
        strategy: StrategyDefinition,
        candles: Sequence[Candle],
        *,
        market: str,
        timeframe: str,
    ) -> None:
        if not strategy.enabled:
            raise StrategyValidationError("strategy is disabled")
        if market != strategy.market:
            raise StrategyValidationError(f"strategy does not support market {market}")
        if timeframe not in strategy.supported_timeframes:
            raise StrategyValidationError(f"strategy does not support timeframe {timeframe}")
        if not candles:
            raise StrategyValidationError("at least one candle is required")
        symbol_id = candles[0].symbol_id
        previous_key: tuple[int, object] | None = None
        for candle in candles:
            if candle.symbol_id != symbol_id:
                raise StrategyValidationError("all candles must use the same symbol_id")
            values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
            if any(not math.isfinite(float(value)) for value in values):
                raise StrategyValidationError("candle OHLCV values must be finite")
            if candle.high < max(candle.open, candle.close) or candle.low > min(
                candle.open, candle.close
            ):
                raise StrategyValidationError("candle high/low does not contain open and close")
            key = (candle.sequence, candle.timestamp)
            if previous_key is not None and key <= previous_key:
                raise StrategyValidationError("candles must be strictly chronological")
            previous_key = key

    @staticmethod
    def _previous_values(
        strategy: StrategyDefinition,
        candles: Sequence[Candle],
        indicator_ids: frozenset[str],
    ) -> dict[str, float]:
        if not indicator_ids:
            return {}
        if len(candles) < 2:
            raise StrategyValidationError("crossing rules require a previous candle")
        by_id = {spec.indicator_id: spec for spec in strategy.required_indicators}
        return {
            indicator_id: evaluate_indicator(by_id[indicator_id], candles[:-1])
            for indicator_id in sorted(indicator_ids)
        }

    def _evaluate_node(
        self,
        node: RuleNode,
        current: dict[str, float],
        previous: dict[str, float],
        traces: list[RuleTrace],
    ) -> bool:
        if isinstance(node, ComparisonRule):
            matched, explanation = self._evaluate_comparison(node, current, previous)
        else:
            child_results = tuple(
                self._evaluate_node(child, current, previous, traces) for child in node.children
            )
            matched = all(child_results) if node.operator.value == "and" else any(child_results)
            explanation = (
                f"{node.rule_id} {node.operator.value.upper()} group "
                f"{'matched' if matched else 'did not match'}."
            )
        traces.append(RuleTrace(rule_id=node.rule_id, matched=matched, explanation=explanation))
        return matched

    @staticmethod
    def _evaluate_comparison(
        rule: ComparisonRule,
        current: dict[str, float],
        previous: dict[str, float],
    ) -> tuple[bool, str]:
        left = _operand_value(rule.left, current)
        operator = rule.operator
        if operator == ComparisonOperator.BETWEEN:
            if rule.lower is None or rule.upper is None:
                raise StrategyValidationError("between rule is missing range operands")
            lower = _operand_value(rule.lower, current)
            upper = _operand_value(rule.upper, current)
            if lower > upper:
                raise StrategyValidationError(f"rule {rule.rule_id} lower value exceeds upper")
            matched = lower <= left <= upper
            detail = f"{lower:.8g} <= {left:.8g} <= {upper:.8g}"
        else:
            if rule.right is None:
                raise StrategyValidationError(f"rule {rule.rule_id} is missing right operand")
            right = _operand_value(rule.right, current)
            if operator == ComparisonOperator.GREATER_THAN:
                matched = left > right
                detail = f"{left:.8g} > {right:.8g}"
            elif operator == ComparisonOperator.LESS_THAN:
                matched = left < right
                detail = f"{left:.8g} < {right:.8g}"
            elif operator == ComparisonOperator.EQUALS:
                matched = abs(left - right) <= rule.equality_tolerance
                detail = f"|{left:.8g} - {right:.8g}| <= {rule.equality_tolerance:.8g}"
            else:
                previous_left = _operand_value(rule.left, previous)
                previous_right = _operand_value(rule.right, previous)
                if operator == ComparisonOperator.CROSSING_ABOVE:
                    matched = previous_left <= previous_right and left > right
                    symbol = "above"
                else:
                    matched = previous_left >= previous_right and left < right
                    symbol = "below"
                detail = (
                    f"{previous_left:.8g}->{left:.8g} crossed {symbol} "
                    f"{previous_right:.8g}->{right:.8g}"
                )
        return matched, f"{rule.rule_id}: {detail} is {matched}."

    @staticmethod
    def _result(
        strategy: StrategyDefinition,
        outcome: StrategyOutcome,
        values: dict[str, float],
        traces: Sequence[RuleTrace],
        explanation: str,
        *,
        valid: bool = True,
    ) -> StrategyEvaluationResult:
        triggered = tuple(trace.rule_id for trace in traces if trace.matched)
        return StrategyEvaluationResult(
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.version,
            outcome=outcome,
            triggered_rule_ids=triggered,
            explanation=explanation,
            indicator_values=values,
            traces=tuple(traces),
            valid=valid,
        )
