"""Unit tests for runtime validation."""

from __future__ import annotations

import pytest

from inference_pipeline.responses.inference_metadata import InferenceMetadata
from ml_runtime import RuntimeValidationError, RuntimeValidator
from ml_runtime.registry.runtime_registry import RuntimeRegistry
from ml_runtime.runtime.runtime_context import RuntimeContext
from models.common import utc_now
from tests.ml_runtime_helpers import StubModelExecutor


@pytest.mark.unit
def test_validator_initialized() -> None:
    validator = RuntimeValidator()
    result = validator.validate_initialized()
    assert result.valid is False
    validator.mark_initialized()
    assert validator.validate_initialized().valid is True


@pytest.mark.unit
def test_validator_executor_exists() -> None:
    registry = RuntimeRegistry()
    validator = RuntimeValidator()
    result = validator.validate_executor_exists("missing", registry)
    assert result.valid is False
    registry.register_executor(StubModelExecutor(), name="Stub", version="1.0.0")
    assert validator.validate_executor_exists("stub-executor", registry).valid is True


@pytest.mark.unit
def test_validator_model_resolved() -> None:
    validator = RuntimeValidator()
    metadata = InferenceMetadata(
        request_id="req-1",
        model_id="model-1",
        version_id="v-1",
        artifact_id="artifact-1",
        config_hash="hash",
        checksum="checksum",
        stage="production",
        correlation_id="c",
        trace_id="t",
        started_at=utc_now(),
    )
    assert validator.validate_model_resolved(metadata).valid is True


@pytest.mark.unit
def test_validator_ensure_valid_raises() -> None:
    validator = RuntimeValidator()
    result = validator.validate_artifact_reference("")
    with pytest.raises(RuntimeValidationError):
        validator.ensure_valid(result)


@pytest.mark.unit
def test_validator_request_metadata() -> None:
    validator = RuntimeValidator()
    context = RuntimeContext(
        session_id="session-1",
        request_id="req-1",
        model_id="model-1",
        model_version="v-1",
        artifact_reference="artifact-1",
        executor_id="executor-1",
        input_metadata={"id": "1"},
        correlation_id="c",
        trace_id="t",
    )
    assert validator.validate_request_metadata(context).valid is True
