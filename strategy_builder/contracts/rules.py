"""Deterministic comparison and logical rule contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from models.common import PlatformModel


class OperandKind(StrEnum):
    """Kinds of values accepted by comparisons."""

    INDICATOR = "indicator"
    CONSTANT = "constant"


class IndicatorOperand(PlatformModel):
    """Reference to a declared indicator."""

    operand_kind: OperandKind = OperandKind.INDICATOR
    indicator_id: str = Field(min_length=1)


class ConstantOperand(PlatformModel):
    """Literal finite numeric comparison value."""

    operand_kind: OperandKind = OperandKind.CONSTANT
    value: float

    @model_validator(mode="after")
    def validate_finite(self) -> ConstantOperand:
        if not (-float("inf") < self.value < float("inf")):
            raise ValueError("constant operand must be finite")
        return self


RuleOperand = IndicatorOperand | ConstantOperand


class ComparisonOperator(StrEnum):
    """Approved deterministic comparison operators."""

    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CROSSING_ABOVE = "crossing_above"
    CROSSING_BELOW = "crossing_below"
    BETWEEN = "between"
    EQUALS = "equals"


class ComparisonRule(PlatformModel):
    """A single typed comparison."""

    rule_id: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_-]*$")
    operator: ComparisonOperator
    left: RuleOperand
    right: RuleOperand | None = None
    lower: RuleOperand | None = None
    upper: RuleOperand | None = None
    equality_tolerance: float = Field(default=0.0, ge=0.0)

    @model_validator(mode="after")
    def validate_shape(self) -> ComparisonRule:
        if self.operator == ComparisonOperator.BETWEEN:
            if self.lower is None or self.upper is None:
                raise ValueError("between requires lower and upper operands")
            if self.right is not None:
                raise ValueError("between does not accept right operand")
        else:
            if self.right is None:
                raise ValueError(f"{self.operator.value} requires right operand")
            if self.lower is not None or self.upper is not None:
                raise ValueError(f"{self.operator.value} does not accept range operands")
        if self.operator != ComparisonOperator.EQUALS and self.equality_tolerance != 0.0:
            raise ValueError("equality_tolerance is only valid for equals")
        return self


class GroupOperator(StrEnum):
    """Approved logical group operators."""

    AND = "and"
    OR = "or"


class RuleGroup(PlatformModel):
    """Recursive deterministic AND/OR rule group."""

    rule_id: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_-]*$")
    operator: GroupOperator
    children: tuple[ComparisonRule | RuleGroup, ...] = Field(min_length=1)


RuleNode = ComparisonRule | RuleGroup
RuleGroup.model_rebuild()
