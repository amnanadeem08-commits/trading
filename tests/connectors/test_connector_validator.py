"""Unit tests for connector validator."""

from __future__ import annotations

from connectors import ConnectorValidator
from connectors.versioning.connector_version import ConnectorVersion
from tests.connectors_helpers import make_adapter_metadata
from versioning.connector_registry import reset_connector_version_registry


def test_validator_passes() -> None:
    validator = ConnectorValidator()
    metadata = make_adapter_metadata()
    result = validator.validate(
        adapter_id="sample-adapter",
        metadata=metadata,
        required_capabilities=("dispatch",),
    )
    assert result.valid is True
    assert result.capabilities_valid is True


def test_validator_missing_metadata() -> None:
    validator = ConnectorValidator()
    result = validator.validate(adapter_id="sample-adapter", metadata=None)
    assert result.valid is False


def test_validator_missing_capabilities() -> None:
    validator = ConnectorValidator()
    metadata = make_adapter_metadata(capabilities=("initialize",))
    result = validator.validate(
        adapter_id="sample-adapter",
        metadata=metadata,
        required_capabilities=("dispatch",),
    )
    assert result.valid is False
    assert result.capabilities_valid is False


def test_validator_id_mismatch() -> None:
    validator = ConnectorValidator()
    metadata = make_adapter_metadata(adapter_id="other")
    result = validator.validate(adapter_id="sample-adapter", metadata=metadata)
    assert result.valid is False


def test_validator_version_incompatible() -> None:
    reset_connector_version_registry()
    version = ConnectorVersion(connector_id="conn-1", version_id="9.9.9")
    version.register(set_current=False)
    validator = ConnectorValidator(version=version)
    result = validator.validate(
        adapter_id="sample-adapter",
        metadata=make_adapter_metadata(),
    )
    assert result.version_compatible is False
