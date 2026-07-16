"""Strategy definition contracts and cross-field validation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from models.common import PlatformModel
from strategy_builder.contracts.indicators import IndicatorKind, IndicatorSpec
from strategy_builder.contracts.rules import (
    ComparisonRule,
    IndicatorOperand,
    RuleGroup,
    RuleNode,
    RuleOperand,
)


class ProtectionKind(StrEnum):
    """Supported deterministic protection references."""

    PERCENTAGE = "percentage"
    ATR_MULTIPLE = "atr_multiple"


class ProtectionRule(PlatformModel):
    """Stop-loss or take-profit distance definition."""

    kind: ProtectionKind
    value: float = Field(gt=0.0)
    indicator_id: str | None = None

    @model_validator(mode="after")
    def validate_reference(self) -> ProtectionRule:
        if self.kind == ProtectionKind.ATR_MULTIPLE and self.indicator_id is None:
            raise ValueError("ATR-multiple protection requires indicator_id")
        if self.kind == ProtectionKind.PERCENTAGE:
            if self.indicator_id is not None:
                raise ValueError("percentage protection does not accept indicator_id")
            if self.value >= 1.0:
                raise ValueError("percentage protection value must be less than 1")
        return self


class TrailingStopConfig(PlatformModel):
    """Optional trailing stop definition."""

    distance_pct: float = Field(gt=0.0, lt=1.0)
    activation_profit_pct: float = Field(default=0.0, ge=0.0, lt=1.0)


class EntryRules(PlatformModel):
    """Directional entry rule trees."""

    buy: RuleNode | None = None
    sell: RuleNode | None = None

    @model_validator(mode="after")
    def validate_direction_present(self) -> EntryRules:
        if self.buy is None and self.sell is None:
            raise ValueError("at least one BUY or SELL entry rule is required")
        return self


def _walk_rules(node: RuleNode) -> tuple[RuleNode, ...]:
    nodes: list[RuleNode] = [node]
    if isinstance(node, RuleGroup):
        for child in node.children:
            nodes.extend(_walk_rules(child))
    return tuple(nodes)


def _operands(rule: ComparisonRule) -> tuple[RuleOperand, ...]:
    values = (rule.left, rule.right, rule.lower, rule.upper)
    return tuple(value for value in values if value is not None)


class StrategyContent(PlatformModel):
    """Validated strategy content shared by drafts and identified definitions."""

    name: str = Field(min_length=1, max_length=120)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    market: str = Field(min_length=1)
    supported_timeframes: tuple[str, ...] = Field(min_length=1)
    entry_rules: EntryRules
    exit_rules: RuleNode
    risk_configuration_reference: str = Field(min_length=1)
    stop_loss_rule: ProtectionRule
    take_profit_rule: ProtectionRule
    trailing_stop: TrailingStopConfig | None = None
    required_indicators: tuple[IndicatorSpec, ...] = Field(min_length=1)
    enabled: bool = True
    description: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)
    schema_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")

    @model_validator(mode="after")
    def validate_definition(self) -> StrategyContent:
        if len(set(self.supported_timeframes)) != len(self.supported_timeframes):
            raise ValueError("supported_timeframes must be unique")
        if any(not timeframe.strip() for timeframe in self.supported_timeframes):
            raise ValueError("supported_timeframes must not contain blank values")
        if len(set(self.tags)) != len(self.tags):
            raise ValueError("tags must be unique")

        indicator_by_id = {spec.indicator_id: spec for spec in self.required_indicators}
        if len(indicator_by_id) != len(self.required_indicators):
            raise ValueError("required indicator IDs must be unique")

        roots = tuple(
            node
            for node in (self.entry_rules.buy, self.entry_rules.sell, self.exit_rules)
            if node is not None
        )
        all_nodes = tuple(item for root in roots for item in _walk_rules(root))
        rule_ids = tuple(node.rule_id for node in all_nodes)
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError("rule IDs must be unique across the strategy")

        for node in all_nodes:
            if not isinstance(node, ComparisonRule):
                continue
            for operand in _operands(node):
                if (
                    isinstance(operand, IndicatorOperand)
                    and operand.indicator_id not in indicator_by_id
                ):
                    raise ValueError(
                        f"rule {node.rule_id} references undeclared indicator "
                        f"{operand.indicator_id}"
                    )

        for protection in (self.stop_loss_rule, self.take_profit_rule):
            if protection.indicator_id is None:
                continue
            indicator = indicator_by_id.get(protection.indicator_id)
            if indicator is None:
                raise ValueError(
                    f"protection references undeclared indicator {protection.indicator_id}"
                )
            if indicator.kind != IndicatorKind.ATR:
                raise ValueError("ATR-multiple protection must reference an ATR indicator")
        return self


class StrategyDraft(StrategyContent):
    """Validated strategy content before deterministic identity is attached."""


class StrategyDefinition(StrategyContent):
    """Immutable, fully auditable deterministic strategy definition."""

    strategy_id: str = Field(min_length=1, pattern=r"^strategy-[a-f0-9]{16}$")
    version_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
