"""Promotion stage tracking."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from model_registry.approval.approval_request import ApprovalRequest
from model_registry.approval.approval_result import ApprovalResult
from model_registry.approval.approval_state import ApprovalState
from model_registry.exceptions import PromotionError
from model_registry.models.model_stage import ModelStage
from models.common import PlatformModel, UTCDateTime, utc_now


class PromotionRecord(PlatformModel):
    """Record of a stage transition for a model version."""

    record_id: str
    model_id: str
    version_id: str
    from_stage: ModelStage
    to_stage: ModelStage
    occurred_at: UTCDateTime


class PromotionRegistry:
    """Tracks model version promotion history."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, PromotionRecord] = {}
        self._by_version: dict[str, tuple[str, ...]] = {}
        self._approval_requests: dict[str, ApprovalRequest] = {}
        self._approval_results: dict[str, ApprovalResult] = {}

    def record_transition(
        self,
        *,
        model_id: str,
        version_id: str,
        from_stage: ModelStage,
        to_stage: ModelStage,
    ) -> PromotionRecord:
        record_id = f"promotion-{uuid4()}"
        record = PromotionRecord(
            record_id=record_id,
            model_id=model_id,
            version_id=version_id,
            from_stage=from_stage,
            to_stage=to_stage,
            occurred_at=utc_now(),
        )
        with self._lock:
            self._records[record_id] = record
            version_records = self._by_version.get(version_id, ())
            self._by_version[version_id] = (*version_records, record_id)
        return record

    def history(self, version_id: str) -> tuple[PromotionRecord, ...]:
        with self._lock:
            record_ids = self._by_version.get(version_id, ())
            return tuple(self._records[rid] for rid in record_ids if rid in self._records)

    def create_approval_request(
        self,
        *,
        model_id: str,
        version_id: str,
        from_stage: ModelStage,
        to_stage: ModelStage,
        requester: str = "platform",
        reason: str = "",
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            request_id=f"approval-{uuid4()}",
            model_id=model_id,
            version_id=version_id,
            from_stage=from_stage,
            to_stage=to_stage,
            requester=requester,
            reason=reason,
            created_at=utc_now(),
        )
        with self._lock:
            self._approval_requests[request.request_id] = request
        return request

    def resolve_approval(
        self,
        request: ApprovalRequest,
        *,
        approved: bool,
        reviewer: str = "platform",
        message: str = "",
    ) -> ApprovalResult:
        if request.state.is_terminal():
            msg = f"approval already resolved: {request.request_id}"
            raise PromotionError(msg)
        state = ApprovalState.APPROVED if approved else ApprovalState.REJECTED
        result = ApprovalResult(
            request_id=request.request_id,
            model_id=request.model_id,
            version_id=request.version_id,
            state=state,
            reviewer=reviewer,
            message=message,
            decided_at=utc_now(),
        )
        resolved = request.model_copy(update={"state": state})
        with self._lock:
            self._approval_requests[request.request_id] = resolved
            self._approval_results[request.request_id] = result
        return result

    def get_approval_request(self, request_id: str) -> ApprovalRequest:
        with self._lock:
            request = self._approval_requests.get(request_id)
        if request is None:
            msg = f"Approval request not found: {request_id}"
            raise PromotionError(msg)
        return request

    def list_approval_requests(self) -> tuple[ApprovalRequest, ...]:
        with self._lock:
            return tuple(self._approval_requests[rid] for rid in sorted(self._approval_requests))
