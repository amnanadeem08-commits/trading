"""Unit tests for ORT executor execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from framework_adapters import ORT_ADAPTER_ID, create_ort_adapter
from framework_adapters.adapters.ort_executor import OrtModelExecutor
from ml_runtime.execution.execution_result import ExecutionStatus
from ml_runtime.runtime.runtime_context import RuntimeContext
from tests.framework_adapters.ort_helpers import generate_identity_model_bytes

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_ort_executor_real_inference_and_health(tmp_path: Path) -> None:
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(generate_identity_model_bytes())
    adapter = create_ort_adapter()
    adapter.load_artifact(
        artifact_reference="local://artifacts/model.onnx",
        metadata={
            "location": {
                "path": "model.onnx",
                "attributes": {"artifact_root": str(tmp_path)},
            }
        },
    )
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
    health = executor.health()
    assert health["loaded"] is True
    assert health["execution_count"] == 0

    context = RuntimeContext(
        session_id="session-ort",
        request_id="request-ort",
        model_id="ort-model",
        model_version="1.0.0",
        artifact_reference="local://artifacts/model.onnx",
        executor_id=ORT_ADAPTER_ID,
        input_metadata={"features": [[1.0], [2.0]]},
        correlation_id="corr-ort",
        trace_id="trace-ort",
    )
    result = executor.execute(context)
    assert result.status == ExecutionStatus.COMPLETED
    assert result.metadata is not None
    assert result.metadata.attributes.get("adapter_id") == ORT_ADAPTER_ID
    assert result.metadata.attributes.get("inference_latency_ms", 0) >= 0
    assert executor.execution_count == 1

    executor.unload()
    assert executor.health()["loaded"] is False
