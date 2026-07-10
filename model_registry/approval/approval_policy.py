"""Approval policy contract."""

from __future__ import annotations

from model_registry.models.model_stage import ModelStage
from models.common import PlatformModel


class ApprovalPolicy(PlatformModel):
    """Policy governing model promotion approvals."""

    policy_id: str
    name: str
    approval_required: bool = True
    allowed_transitions: tuple[tuple[ModelStage, ModelStage], ...] = (
        (ModelStage.DRAFT, ModelStage.STAGING),
        (ModelStage.STAGING, ModelStage.VALIDATION),
        (ModelStage.VALIDATION, ModelStage.APPROVED),
        (ModelStage.APPROVED, ModelStage.PRODUCTION),
        (ModelStage.PRODUCTION, ModelStage.ARCHIVED),
    )

    def allows(self, *, from_stage: ModelStage, to_stage: ModelStage) -> bool:
        return (from_stage, to_stage) in self.allowed_transitions
