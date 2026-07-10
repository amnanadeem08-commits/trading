"""Approval request contract."""

from __future__ import annotations

from model_registry.approval.approval_state import ApprovalState
from model_registry.models.model_stage import ModelStage
from models.common import PlatformModel, UTCDateTime


class ApprovalRequest(PlatformModel):
    """Request to approve a model version promotion."""

    request_id: str
    model_id: str
    version_id: str
    from_stage: ModelStage
    to_stage: ModelStage
    requester: str = "platform"
    reason: str = ""
    state: ApprovalState = ApprovalState.PENDING
    created_at: UTCDateTime
