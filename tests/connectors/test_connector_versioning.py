"""Unit tests for connector versioning."""

from __future__ import annotations

from connectors import ConnectorVersion
from versioning.connector_registry import reset_connector_version_registry


def test_connector_version_register() -> None:
    reset_connector_version_registry()
    version = ConnectorVersion(
        connector_id="conn-1",
        version_id="1.0.0",
        description="Initial version",
    )
    registered = version.register()
    assert registered.version_id == "1.0.0"
    versions = ConnectorVersion.list_versions()
    assert len(versions) >= 1


def test_connector_version_to_version_info() -> None:
    version = ConnectorVersion(
        connector_id="conn-1",
        version_id="2.0.0",
        artifact_type="adapter",
        description="Updated",
    )
    info = version.to_version_info()
    assert info.version_id == "2.0.0"


def test_connector_version_is_compatible() -> None:
    reset_connector_version_registry()
    version = ConnectorVersion(connector_id="conn-1", version_id="1.0.0")
    assert version.is_compatible() is True
    version.register()
    assert version.is_compatible() is True
