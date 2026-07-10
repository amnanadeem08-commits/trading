"""Execution-layer validation for inference requests."""

from __future__ import annotations

from typing import Any

from inference_pipeline.requests.inference_request import InferenceRequest
from inference_pipeline.runtime.input_schema import FeatureSpec, InputSchema, OutputType
from inference_pipeline.validation.validation_result import InferenceValidationResult


class InferenceExecutionValidator:
    """Validates feature binding and execution request completeness."""

    _SUPPORTED_DTYPES = frozenset({"float32", "float64", "int32", "int64"})

    def validate_execution_request(
        self,
        *,
        model_id: str,
        schema: InputSchema,
        features: dict[str, Any],
        request_id: str = "",
    ) -> InferenceValidationResult:
        errors: list[str] = []
        if not model_id.strip():
            errors.append("model_id must not be empty")
        if not schema.features:
            errors.append("input schema must define features")
        if not features:
            errors.append("features must not be empty")
        if errors:
            return InferenceValidationResult.failure(
                *errors, request_id=request_id, model_id=model_id
            )
        return self.validate_features(schema=schema, features=features, request_id=request_id)

    def validate_features(
        self,
        *,
        schema: InputSchema,
        features: dict[str, Any],
        request_id: str = "",
    ) -> InferenceValidationResult:
        errors: list[str] = []
        for spec in schema.features:
            errors.extend(self._validate_feature_spec(spec, features))
        if len(features) > len(schema.features):
            extra = set(features) - {spec.name for spec in schema.features}
            if extra:
                errors.append(f"unexpected features: {', '.join(sorted(extra))}")
        if errors:
            return InferenceValidationResult.failure(*errors, request_id=request_id)
        return InferenceValidationResult.success(request_id=request_id)

    def validate_bound_input(
        self,
        *,
        schema: InputSchema,
        bound_input: dict[str, object],
    ) -> InferenceValidationResult:
        errors: list[str] = []
        matrix = bound_input.get("input")
        if not isinstance(matrix, list) or not matrix:
            errors.append("bound input matrix must not be empty")
        else:
            row = matrix[0]
            if not isinstance(row, list):
                errors.append("bound input row must be a list")
            elif len(row) != len(schema.features):
                errors.append("bound feature count does not match schema")
        dtype = str(bound_input.get("dtype", ""))
        if dtype and dtype not in self._SUPPORTED_DTYPES:
            errors.append(f"unsupported dtype: {dtype}")
        if errors:
            return InferenceValidationResult.failure(*errors)
        return InferenceValidationResult.success()

    def validate_output_schema(self, *, output_type: OutputType) -> InferenceValidationResult:
        if output_type not in OutputType:
            return InferenceValidationResult.failure(f"unsupported output type: {output_type}")
        return InferenceValidationResult.success()

    def validate_orchestration_request(
        self, request: InferenceRequest
    ) -> InferenceValidationResult:
        errors: list[str] = []
        if not request.request_id.strip():
            errors.append("request_id must not be empty")
        if not request.model_id.strip():
            errors.append("model_id must not be empty")
        if errors:
            return InferenceValidationResult.failure(*errors, request_id=request.request_id)
        return InferenceValidationResult.success(
            request_id=request.request_id,
            model_id=request.model_id,
        )

    def _validate_feature_spec(
        self,
        spec: FeatureSpec,
        features: dict[str, Any],
    ) -> list[str]:
        errors: list[str] = []
        if spec.dtype not in self._SUPPORTED_DTYPES:
            errors.append(f"unsupported dtype for feature {spec.name}: {spec.dtype}")
        if spec.name not in features:
            if spec.optional and spec.default is not None:
                return errors
            errors.append(f"missing required feature: {spec.name}")
            return errors
        value = features[spec.name]
        if not self._is_compatible_value(value, spec.dtype):
            errors.append(f"incompatible dtype for feature {spec.name}")
        if spec.shape and not self._shape_matches(value, spec.shape):
            errors.append(f"feature shape mismatch for {spec.name}")
        return errors

    @staticmethod
    def _is_compatible_value(value: Any, dtype: str) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, (list, tuple)):
            return all(
                isinstance(item, (int, float)) and not isinstance(item, bool) for item in value
            )
        if dtype.startswith("float"):
            return isinstance(value, (int, float))
        if dtype.startswith("int"):
            return isinstance(value, int) and not isinstance(value, bool)
        return False

    @staticmethod
    def _shape_matches(value: Any, shape: tuple[int, ...]) -> bool:
        if not shape:
            return True
        if isinstance(value, (list, tuple)) and len(shape) == 1 and shape[0] not in {0}:
            return len(value) == shape[0]
        return True
