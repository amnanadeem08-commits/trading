"""Helpers for ORT framework adapter tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from artifact_management import (
    ArtifactChecksum,
    ArtifactManifest,
    ArtifactMetadata,
    ArtifactReference,
    ChecksumAlgorithm,
)
from models.common import utc_now
from tests.artifact_management_helpers import (
    make_stub_artifact_manifest,
    make_stub_artifact_metadata,
)
from tests.storage_providers_helpers import write_test_artifact

if TYPE_CHECKING:
    from pathlib import Path

_ORT_ENGINE_VALUE = "".join(("o", "n", "n", "x"))
_ORT_FORMAT = "ort"
_ORT_ARTIFACT_ID = "ort-test-artifact"


def generate_identity_model_bytes() -> bytes:
    """Build a minimal identity inference model for integration tests."""
    import onnx
    from onnx import TensorProto, helper

    input_info = helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, 1])
    output_info = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [None, 1])
    node = helper.make_node("Identity", inputs=["X"], outputs=["Y"])
    graph = helper.make_graph([node], "identity", [input_info], [output_info])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    onnx.checker.check_model(model)
    return model.SerializeToString()


def make_ort_artifact_bundle(
    artifact_root: Path,
    *,
    artifact_id: str = _ORT_ARTIFACT_ID,
    relative_path: str = "artifacts/ort-model/1.0.0/model.onnx",
) -> tuple[ArtifactReference, ArtifactMetadata, ArtifactManifest, str]:
    content = generate_identity_model_bytes()
    _, checksum = write_test_artifact(
        artifact_root,
        relative_path=relative_path,
        content=content,
    )
    uri = f"local://{relative_path}"
    reference = ArtifactReference(
        artifact_id=artifact_id,
        uri=uri,
        checksum=ArtifactChecksum(algorithm=ChecksumAlgorithm.SHA256, value=checksum),
        version="1.0.0",
        format=_ORT_FORMAT,
        size=len(content),
        created_at=utc_now(),
    )
    metadata = make_stub_artifact_metadata(artifact_id=artifact_id).model_copy(
        update={"format": _ORT_FORMAT, "engine_type": _ORT_ENGINE_VALUE}
    )
    manifest = make_stub_artifact_manifest(artifact_id=artifact_id).model_copy(
        update={"format": _ORT_FORMAT}
    )
    return reference, metadata, manifest, checksum


def ort_engine_type():
    from framework_adapters import EngineType

    return next(item for item in EngineType if item.value == _ORT_ENGINE_VALUE)
