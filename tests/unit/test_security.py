"""Unit tests for security scaffolds."""

from __future__ import annotations

import pytest

from security import (
    Identity,
    Permission,
    PermissionAction,
    Role,
    SecurityAuditEvent,
    SecurityEventType,
)


@pytest.mark.unit
def test_identity_has_role() -> None:
    identity = Identity(identity_id="user-1", roles=("admin",))
    assert identity.has_role("admin") is True
    assert identity.has_role("viewer") is False


@pytest.mark.unit
def test_role_permission_models() -> None:
    permission = Permission(resource="orders", action=PermissionAction.WRITE)
    role = Role(role_id="trader", name="Trader", permissions=(permission,))
    assert role.permissions[0].resource == "orders"


@pytest.mark.unit
def test_security_audit_event_contract() -> None:
    event = SecurityAuditEvent(
        event_type=SecurityEventType.AUTH_FAILURE,
        message="invalid credentials",
    )
    assert event.event_type == SecurityEventType.AUTH_FAILURE
