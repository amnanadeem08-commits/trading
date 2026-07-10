"""Approval result contract."""

from __future__ import annotations

from model_registry.approval.approval_state import ApprovalState
from models.common import PlatformModel, UTCDateTime


class ApprovalResult(PlatformModel):
    """Outcome of a promotion approval decision."""

    request_id: str
    model_id: str
    version_id: str
    state: ApprovalState
    reviewer: str = "platform"
    message: str = ""
    decided_at: UTCDateTime

    @property
    def approved(self) -> bool:
        return self.state == ApprovalState.APPROVED
