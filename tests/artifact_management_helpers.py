"""Helpers for artifact management tests."""

from __future__ import annotations

from artifact_management import (
    ArtifactChecksum,
    ArtifactManifest,
    ArtifactMetadata,
    ArtifactReference,
    ChecksumAlgorithm,
    FrameworkAdapterArtifactBridge,
    build_artifact_bridge,
)
from framework_adapters import StubFrameworkAdapter, create_stub_adapter
from models.common import utc_now

STUB_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
STUB_ARTIFACT_ID = "stub-artifact-1"
STUB_ARTIFACT_URI = "local://artifacts/stub-model/1.0.0/model.stub"


def make_stub_artifact_reference(
    *,
    artifact_id: str = STUB_ARTIFACT_ID,
    uri: str = STUB_ARTIFACT_URI,
) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=artifact_id,
        uri=uri,
        checksum=ArtifactChecksum(algorithm=ChecksumAlgorithm.SHA256, value=STUB_SHA256),
        version="1.0.0",
        format="stub",
        size=1024,
        created_at=utc_now(),
    )


def make_stub_artifact_metadata(
    *,
    artifact_id: str = STUB_ARTIFACT_ID,
) -> ArtifactMetadata:
    return ArtifactMetadata(
        artifact_id=artifact_id,
        name="Stub Artifact",
        version="1.0.0",
        format="stub",
        engine_type="stub",
        description="Stub artifact for architecture validation",
        registered_at=utc_now(),
    )


def make_stub_artifact_manifest(
    *,
    artifact_id: str = STUB_ARTIFACT_ID,
) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=artifact_id,
        name="Stub Artifact",
        version="1.0.0",
        engine_type="stub",
        files=("model.stub", "manifest.json"),
        dependencies=(),
        runtime_metadata={"sandbox": True},
        compatibility_metadata={"min_runtime": "1.0.0"},
    )


def make_stub_artifact_bundle(
    *,
    artifact_id: str = STUB_ARTIFACT_ID,
    uri: str = STUB_ARTIFACT_URI,
) -> tuple[ArtifactReference, ArtifactMetadata, ArtifactManifest]:
    return (
        make_stub_artifact_reference(artifact_id=artifact_id, uri=uri),
        make_stub_artifact_metadata(artifact_id=artifact_id),
        make_stub_artifact_manifest(artifact_id=artifact_id),
    )


def make_artifact_bridge() -> FrameworkAdapterArtifactBridge:
    return build_artifact_bridge()


def make_stub_framework_adapter(
    *,
    adapter_id: str = STUB_ARTIFACT_ID,
) -> StubFrameworkAdapter:
    return create_stub_adapter()
