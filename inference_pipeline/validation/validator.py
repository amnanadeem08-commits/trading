"""Inference pipeline validator."""

from __future__ import annotations

from inference_pipeline.exceptions import InferenceValidationError
from inference_pipeline.requests.inference_batch_request import InferenceBatchRequest
from inference_pipeline.requests.inference_request import InferenceRequest
from inference_pipeline.responses.inference_metadata import InferenceMetadata
from inference_pipeline.validation.validation_result import InferenceValidationResult
from model_registry.models.model_stage import ModelStage
from model_registry.models.model_version import ModelVersion
from model_registry.registry.model_registry import ModelRegistryStore


class InferenceValidator:
    """Validates inference requests and model resolution prerequisites."""

    def __init__(self, *, production_only: bool = True) -> None:
        self._production_only = production_only

    def validate_request(self, request: InferenceRequest) -> InferenceValidationResult:
        errors: list[str] = []
        if not request.request_id.strip():
            errors.append("request_id must not be empty")
        if not request.model_id.strip():
            errors.append("model_id must not be empty")
        if not request.input_metadata:
            errors.append("input_metadata must not be empty")
        if errors:
            return InferenceValidationResult.failure(*errors, request_id=request.request_id)
        return InferenceValidationResult.success(
            request_id=request.request_id,
            model_id=request.model_id,
        )

    def validate_batch_request(self, request: InferenceBatchRequest) -> InferenceValidationResult:
        errors: list[str] = []
        if not request.batch_id.strip():
            errors.append("batch_id must not be empty")
        if not request.model_id.strip():
            errors.append("model_id must not be empty")
        if not request.input_metadata_batch:
            errors.append("input_metadata_batch must not be empty")
        if errors:
            return InferenceValidationResult.failure(*errors, request_id=request.batch_id)
        return InferenceValidationResult.success(
            request_id=request.batch_id,
            model_id=request.model_id,
        )

    def validate_model_exists(
        self,
        model_id: str,
        registry: ModelRegistryStore,
    ) -> InferenceValidationResult:
        from model_registry.exceptions import ModelNotFoundError

        try:
            registry.lookup(model_id)
        except ModelNotFoundError:
            return InferenceValidationResult.failure(
                f"Model not found: {model_id}",
                request_id=None,
            )
        return InferenceValidationResult.success(model_id=model_id)

    def validate_production_version(self, version: ModelVersion) -> InferenceValidationResult:
        if self._production_only and version.stage != ModelStage.PRODUCTION:
            return InferenceValidationResult.failure(
                f"Version {version.version_id} is not in production stage",
                request_id=None,
            )
        if not version.artifact_id.strip():
            return InferenceValidationResult.failure("artifact_id must not be empty")
        if not version.dataset_id.strip():
            return InferenceValidationResult.failure("dataset_id must not be empty")
        if not version.checksum.strip():
            return InferenceValidationResult.failure("checksum must not be empty")
        return InferenceValidationResult.success(model_id=version.model_id)

    def validate_metadata(self, metadata: InferenceMetadata) -> InferenceValidationResult:
        errors: list[str] = []
        if not metadata.request_id.strip():
            errors.append("request_id must not be empty")
        if not metadata.version_id.strip():
            errors.append("version_id must not be empty")
        if not metadata.artifact_id.strip():
            errors.append("artifact_id must not be empty")
        if errors:
            return InferenceValidationResult.failure(*errors, request_id=metadata.request_id)
        return InferenceValidationResult.success(request_id=metadata.request_id)

    def ensure_valid(self, result: InferenceValidationResult) -> None:
        if not result.valid:
            message = result.errors[0] if result.errors else "validation failed"
            raise InferenceValidationError(message)
