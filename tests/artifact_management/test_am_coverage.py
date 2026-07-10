"""Coverage tests for artifact management."""

from __future__ import annotations

import pytest

from artifact_management import (
    ArtifactChecksum,
    ArtifactManagementError,
    ArtifactScheme,
    ArtifactVersionRegistry,
    ChecksumAlgorithm,
)
from artifact_management.models.artifact_location import ArtifactLocation as LocationModel
from tests.artifact_management_helpers import make_stub_artifact_reference


@pytest.mark.unit
def test_artifact_checksum_format_validation() -> None:
    valid = ArtifactChecksum(algorithm=ChecksumAlgorithm.SHA256, value="a" * 64)
    invalid = ArtifactChecksum(algorithm=ChecksumAlgorithm.SHA256, value="short")
    assert valid.validate_format() is True
    assert invalid.validate_format() is False


@pytest.mark.unit
def test_artifact_location_from_uri_schemes() -> None:
    for uri, scheme in (
        ("file:///tmp/model.stub", ArtifactScheme.FILE),
        ("s3://bucket/path/model.stub", ArtifactScheme.S3),
        ("gs://bucket/path/model.stub", ArtifactScheme.GS),
        ("azure://container/path/model.stub", ArtifactScheme.AZURE),
        ("http://example.com/model.stub", ArtifactScheme.HTTP),
    ):
        location = LocationModel.from_uri(uri)
        assert location.scheme == scheme


@pytest.mark.unit
def test_artifact_location_rejects_unsupported_scheme() -> None:
    with pytest.raises(ValueError):
        LocationModel.from_uri("ftp://files/model.stub")


@pytest.mark.unit
def test_version_registry_rejects_empty_id() -> None:
    registry = ArtifactVersionRegistry()
    with pytest.raises(ArtifactManagementError):
        registry.register(version_id="", framework_schema="1.0.0")


@pytest.mark.unit
def test_stub_artifact_reference_fields() -> None:
    reference = make_stub_artifact_reference()
    assert reference.format == "stub"
    assert reference.checksum.algorithm == ChecksumAlgorithm.SHA256
