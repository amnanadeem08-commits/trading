"""ML runtime validator."""

from __future__ import annotations

from inference_pipeline.responses.inference_metadata import InferenceMetadata
from ml_runtime.exceptions import RuntimeValidationError
from ml_runtime.registry.runtime_registry import RuntimeRegistry
from ml_runtime.runtime.runtime_context import RuntimeContext
from ml_runtime.validation.validation_result import RuntimeValidationResult


class RuntimeValidator:
    """Validates runtime prerequisites before execution."""

    def __init__(self, *, require_initialized: bool = True) -> None:
        self._require_initialized = require_initialized
        self._initialized = False

    def mark_initialized(self) -> None:
        self._initialized = True

    def validate_initialized(self) -> RuntimeValidationResult:
        if self._require_initialized and not self._initialized:
            return RuntimeValidationResult.failure("runtime is not initialized")
        return RuntimeValidationResult.success()

    def validate_executor_exists(
        self,
        executor_id: str,
        registry: RuntimeRegistry,
    ) -> RuntimeValidationResult:
        if not executor_id.strip():
            return RuntimeValidationResult.failure("executor_id must not be empty")
        if registry.metadata(executor_id) is None:
            return RuntimeValidationResult.failure(f"Executor not found: {executor_id}")
        return RuntimeValidationResult.success(executor_id=executor_id)

    def validate_model_resolved(self, metadata: InferenceMetadata) -> RuntimeValidationResult:
        errors: list[str] = []
        if not metadata.model_id.strip():
            errors.append("model_id must not be empty")
        if not metadata.version_id.strip():
            errors.append("model_version must not be empty")
        if not metadata.artifact_id.strip():
            errors.append("artifact_reference must not be empty")
        if errors:
            return RuntimeValidationResult.failure(*errors, request_id=metadata.request_id)
        return RuntimeValidationResult.success(
            request_id=metadata.request_id,
            model_id=metadata.model_id,
        )

    def validate_artifact_reference(self, artifact_reference: str) -> RuntimeValidationResult:
        if not artifact_reference.strip():
            return RuntimeValidationResult.failure("artifact_reference must not be empty")
        return RuntimeValidationResult.success()

    def validate_request_metadata(self, context: RuntimeContext) -> RuntimeValidationResult:
        errors: list[str] = []
        if not context.request_id.strip():
            errors.append("request_id must not be empty")
        if not context.input_metadata:
            errors.append("input_metadata must not be empty")
        if not context.correlation_id.strip():
            errors.append("correlation_id must not be empty")
        if not context.trace_id.strip():
            errors.append("trace_id must not be empty")
        if errors:
            return RuntimeValidationResult.failure(*errors, request_id=context.request_id)
        return RuntimeValidationResult.success(
            request_id=context.request_id,
            model_id=context.model_id,
            executor_id=context.executor_id,
        )

    def ensure_valid(self, result: RuntimeValidationResult) -> None:
        if not result.valid:
            message = result.errors[0] if result.errors else "validation failed"
            raise RuntimeValidationError(message)
