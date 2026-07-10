"""Security audit hook interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class SecurityEventType(StrEnum):
    """Security audit event types."""

    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    PERMISSION_DENIED = "permission_denied"
    SECRET_ACCESSED = "secret_accessed"
    TOKEN_ISSUED = "token_issued"


class SecurityAuditEvent(PlatformModel):
    """Security audit event contract."""

    event_type: SecurityEventType
    identity_id: str | None = None
    resource: str | None = None
    message: str = Field(min_length=1)
    recorded_at: UTCDateTime = Field(default_factory=utc_now)


class SecurityAuditHook(ABC):
    """Interface for recording security audit events."""

    @abstractmethod
    def record(self, event: SecurityAuditEvent) -> None:
        """Record a security audit event."""
