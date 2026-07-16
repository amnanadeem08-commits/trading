"""Public strategy builder contracts."""

from strategy_builder.contracts.evaluation import (
    PositionContext,
    PositionSide,
    RuleTrace,
    StrategyEvaluationResult,
    StrategyOutcome,
)
from strategy_builder.contracts.indicators import CandleField, IndicatorKind, IndicatorSpec
from strategy_builder.contracts.rules import (
    ComparisonOperator,
    ComparisonRule,
    ConstantOperand,
    GroupOperator,
    IndicatorOperand,
    OperandKind,
    RuleGroup,
    RuleNode,
    RuleOperand,
)
from strategy_builder.contracts.strategy import (
    EntryRules,
    ProtectionKind,
    ProtectionRule,
    StrategyDefinition,
    StrategyDraft,
    TrailingStopConfig,
)

__all__ = [
    "CandleField",
    "ComparisonOperator",
    "ComparisonRule",
    "ConstantOperand",
    "EntryRules",
    "GroupOperator",
    "IndicatorKind",
    "IndicatorOperand",
    "IndicatorSpec",
    "OperandKind",
    "PositionContext",
    "PositionSide",
    "ProtectionKind",
    "ProtectionRule",
    "RuleGroup",
    "RuleNode",
    "RuleOperand",
    "RuleTrace",
    "StrategyDefinition",
    "StrategyDraft",
    "StrategyEvaluationResult",
    "StrategyOutcome",
    "TrailingStopConfig",
]
