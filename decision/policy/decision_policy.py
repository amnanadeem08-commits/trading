"""Decision policy contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from decision.engine.decision_context import DecisionContext
from decision.policy.policy_result import PolicyResult
from models.common import PlatformModel


class PolicyMetadata(PlatformModel):
    """Metadata for a registered decision policy."""

    policy_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)


class DecisionPolicy(ABC):
    """Generic decision policy contract."""

    @abstractmethod
    def policy_id(self) -> str:
        """Return the unique policy identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the human-readable policy name."""

    @abstractmethod
    def version(self) -> str:
        """Return the policy version."""

    def metadata(self) -> PolicyMetadata:
        """Return policy metadata."""
        return PolicyMetadata(
            policy_id=self.policy_id(),
            name=self.name(),
            version=self.version(),
        )

    @abstractmethod
    def evaluate(
        self,
        context: DecisionContext,
        *,
        ai_output: dict[str, Any],
        ml_output: dict[str, Any],
    ) -> PolicyResult:
        """Evaluate inputs against this policy."""
