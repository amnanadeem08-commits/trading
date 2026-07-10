"""Core runtime context."""

from __future__ import annotations

from pydantic import Field

from core.context.audit_context import AuditContext
from core.context.execution_context import ExecutionContext
from core.context.identity_context import IdentityContext
from core.context.operation_context import OperationContext
from core.context.request_context import RequestContext
from core.context.security_context import SecurityContext
from models.common import PlatformModel


class CoreContext(PlatformModel):
    """Shared runtime context propagated across pipeline layers."""

    trace_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    request: RequestContext
    execution: ExecutionContext
    operation: OperationContext
    identity: IdentityContext
    security: SecurityContext
    audit: AuditContext
    dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    plugin_ids: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)
