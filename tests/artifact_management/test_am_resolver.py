"""Unit tests for artifact resolver."""

from __future__ import annotations

import pytest

from artifact_management import ArtifactResolutionError, ArtifactResolver, URIResolver
from artifact_management.models.artifact_location import ArtifactLocation, ArtifactScheme
from tests.artifact_management_helpers import make_stub_artifact_bundle


@pytest.mark.unit
def test_uri_resolver_parses_local_uri() -> None:
    resolver = URIResolver()
    location = resolver.resolve("local://artifacts/stub-model/model.stub")
    assert location.scheme.value == "local"
    assert location.uri.startswith("local://")


@pytest.mark.unit
def test_uri_resolver_rejects_invalid_uri() -> None:
    resolver = URIResolver()
    with pytest.raises(ArtifactResolutionError):
        resolver.resolve("invalid-uri")


@pytest.mark.unit
def test_artifact_resolver_requires_storage_provider_location() -> None:
    resolver = ArtifactResolver()
    reference, metadata, manifest = make_stub_artifact_bundle()
    with pytest.raises(ArtifactResolutionError):
        resolver.resolve(reference=reference, metadata=metadata, manifest=manifest)


@pytest.mark.unit
def test_artifact_resolver_accepts_pre_resolved_reference() -> None:
    resolver = ArtifactResolver()
    reference, metadata, manifest = make_stub_artifact_bundle()
    located = reference.model_copy(
        update={
            "location": ArtifactLocation(
                uri=reference.uri,
                scheme=ArtifactScheme.LOCAL,
                path="artifacts/stub-model/1.0.0/model.stub",
            )
        }
    )
    resolved = resolver.resolve(reference=located, metadata=metadata, manifest=manifest)
    assert resolved.location is not None
    assert resolved.location.scheme == ArtifactScheme.LOCAL


@pytest.mark.unit
def test_artifact_resolver_rejects_mismatched_metadata() -> None:
    resolver = ArtifactResolver()
    reference, metadata, manifest = make_stub_artifact_bundle()
    located = reference.model_copy(
        update={
            "location": ArtifactLocation(
                uri=reference.uri,
                scheme=ArtifactScheme.LOCAL,
                path="artifacts/stub-model/1.0.0/model.stub",
            )
        }
    )
    bad_metadata = metadata.model_copy(update={"artifact_id": "other"})
    with pytest.raises(ArtifactResolutionError):
        resolver.resolve(reference=located, metadata=bad_metadata, manifest=manifest)
