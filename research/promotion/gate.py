"""Research promotion gate interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from models.common import PlatformModel


class PromotionDecision(StrEnum):
    """Outcome of a promotion gate evaluation."""

    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class PromotionRequest(PlatformModel):
    """Request to promote research artifact into production."""

    artifact_name: str
    artifact_version: str
    source_path: str
    requested_by: str = "research"


class PromotionResult(PlatformModel):
    """Result of promotion gate evaluation."""

    decision: PromotionDecision
    artifact_name: str
    artifact_version: str
    rationale: str


class PromotionGate(ABC):
    """Interface for promoting research artifacts into production."""

    @abstractmethod
    def evaluate(self, request: PromotionRequest) -> PromotionResult:
        """Evaluate whether a research artifact may enter production."""
