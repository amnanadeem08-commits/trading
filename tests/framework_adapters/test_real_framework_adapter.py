"""Unit tests for the concrete ORT framework adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from framework_adapters import (
    ORT_ADAPTER_ID,
    AdapterCapability,
    AdapterLoadError,
    OrtFrameworkAdapter,
    create_ort_adapter,
)
from framework_adapters.adapters.ort_executor import OrtModelExecutor
from tests.framework_adapters.ort_helpers import generate_identity_model_bytes, ort_engine_type

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_ort_adapter_contract_and_environment() -> None:
    adapter = create_ort_adapter()
    assert adapter.adapter_id() == ORT_ADAPTER_ID
    assert adapter.engine_type() == ort_engine_type()
    assert AdapterCapability.LOAD_ARTIFACT in adapter.capabilities()
    environment = adapter.validate_environment()
    assert environment["status"] == "healthy"
    assert environment["framework_available"] is True


@pytest.mark.unit
def test_ort_adapter_loads_real_model_and_executes(tmp_path: Path) -> None:
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(generate_identity_model_bytes())
    adapter = create_ort_adapter()
    load_result = adapter.load_artifact(
        artifact_reference="local://artifacts/model.onnx",
        metadata={
            "location": {
                "path": "model.onnx",
                "attributes": {"artifact_root": str(tmp_path)},
            }
        },
    )
    assert load_result["loaded"] is True
    assert adapter.artifact_loaded is True

    executor = adapter.create_executor()
    assert isinstance(executor, OrtModelExecutor)
    executor.load(
        artifact_reference="local://artifacts/model.onnx",
        metadata={
            "location": {
                "path": "model.onnx",
                "attributes": {"artifact_root": str(tmp_path)},
            }
        },
    )
    from ml_runtime.runtime.runtime_context import RuntimeContext

    context = RuntimeContext(
        session_id="session-1",
        request_id="request-1",
        model_id="model-1",
        model_version="1.0.0",
        artifact_reference="local://artifacts/model.onnx",
        executor_id=ORT_ADAPTER_ID,
        input_metadata={"input": [[2.5]]},
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = executor.execute(context)
    assert result.status.value == "completed"
    assert result.metadata is not None
    outputs = result.metadata.attributes.get("inference_outputs")
    assert outputs == [[[2.5]]]
    adapter.shutdown()
    assert adapter.artifact_loaded is False


@pytest.mark.unit
def test_ort_adapter_rejects_missing_model_path() -> None:
    adapter = OrtFrameworkAdapter()
    with pytest.raises(AdapterLoadError):
        adapter.load_artifact(artifact_reference="local://missing.onnx", metadata={})
