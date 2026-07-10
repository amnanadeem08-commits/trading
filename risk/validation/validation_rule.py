"""Validation rule contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from models.common import PlatformModel
from risk.engine.risk_context import RiskContext


class RuleMetadata(PlatformModel):
    """Metadata for a validation rule."""

    rule_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1, default="1.0.0")
    description: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)


class ValidationRule(ABC):
    """Generic validation rule contract."""

    @abstractmethod
    def rule_id(self) -> str:
        """Return the unique rule identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the human-readable rule name."""

    def metadata(self) -> RuleMetadata:
        """Return rule metadata."""
        return RuleMetadata(rule_id=self.rule_id(), name=self.name())

    @abstractmethod
    def validate(self, context: RiskContext, *, input_data: dict[str, Any]) -> bool:
        """Validate input data against this rule."""
