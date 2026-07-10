"""Unit tests for artifact validator."""

from __future__ import annotations

import pytest

from artifact_management import ArtifactRegistry, ArtifactValidationError, ArtifactValidator
from tests.artifact_management_helpers import (
    make_stub_artifact_bundle,
)


@pytest.mark.unit
def test_validator_accepts_stub_artifact() -> None:
    validator = ArtifactValidator()
    reference, metadata, manifest = make_stub_artifact_bundle()
    result = validator.validate_reference(
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    assert result.valid is True


@pytest.mark.unit
def test_validator_rejects_invalid_uri() -> None:
    validator = ArtifactValidator()
    reference, metadata, manifest = make_stub_artifact_bundle(uri="bad-uri")
    result = validator.validate_reference(
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    assert result.valid is False


@pytest.mark.unit
def test_validator_rejects_duplicate_registration() -> None:
    registry = ArtifactRegistry()
    validator = ArtifactValidator(registry=registry)
    reference, metadata, manifest = make_stub_artifact_bundle()
    registry.register(metadata=metadata, manifest=manifest, reference=reference)
    result = validator.validate_reference(
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    assert result.valid is False


@pytest.mark.unit
def test_validator_ensure_valid_raises() -> None:
    validator = ArtifactValidator()
    reference, metadata, manifest = make_stub_artifact_bundle()
    bad = metadata.model_copy(update={"artifact_id": ""})
    result = validator.validate_reference(reference=reference, metadata=bad, manifest=manifest)
    with pytest.raises(ArtifactValidationError):
        validator.ensure_valid(result)
