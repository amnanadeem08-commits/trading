"""Input binding and schema validation."""

from __future__ import annotations

import time
from typing import Any

from inference_pipeline.runtime.feature_binding import FeatureBinding
from inference_pipeline.runtime.input_schema import FeatureSpec, InputSchema
from inference_pipeline.validation.execution_validator import InferenceExecutionValidator


class InputBinding:
    """Validates and binds feature data to model input tensors."""

    def __init__(
        self,
        *,
        validator: InferenceExecutionValidator | None = None,
        feature_binding: FeatureBinding | None = None,
    ) -> None:
        self._validator = validator or InferenceExecutionValidator()
        self._feature_binding = feature_binding or FeatureBinding()

    def bind(
        self,
        *,
        schema: InputSchema,
        features: dict[str, Any],
    ) -> tuple[dict[str, object], float]:
        """Validate schema compatibility and bind features to model input."""
        started = time.monotonic() * 1000.0
        validation = self._validator.validate_features(schema=schema, features=features)
        if not validation.valid:
            message = validation.errors[0] if validation.errors else "feature validation failed"
            raise ValueError(message)
        payload, map_duration_ms = self._feature_binding.bind(schema=schema, features=features)
        bind_duration_ms = max(0.0, time.monotonic() * 1000.0 - started)
        return payload, bind_duration_ms + map_duration_ms

    @staticmethod
    def expected_feature_count(schema: InputSchema) -> int:
        return len(schema.features)

    @staticmethod
    def expected_shape(spec: FeatureSpec) -> tuple[int, ...]:
        return spec.shape
