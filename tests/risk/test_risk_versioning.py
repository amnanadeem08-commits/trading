"""Unit tests for risk versioning."""

from __future__ import annotations

from risk import RiskVersion
from versioning.connector_registry import reset_connector_version_registry


def test_risk_version_register() -> None:
    reset_connector_version_registry()
    version = RiskVersion(
        risk_id="policy-1",
        version_id="1.0.0",
        description="Initial version",
    )
    registered = version.register()
    assert registered.version_id == "1.0.0"
    versions = RiskVersion.list_versions()
    assert len(versions) >= 1


def test_risk_version_to_version_info() -> None:
    version = RiskVersion(
        risk_id="policy-1",
        version_id="2.0.0",
        artifact_type="policy",
        description="Updated",
    )
    info = version.to_version_info()
    assert info.version_id == "2.0.0"
