"""Feature schema validator."""

from __future__ import annotations

from feature_engineering.models.feature_vector import FeatureVector
from feature_engineering.schema.feature_schema import FeatureSchema
from feature_engineering.validation.validation_result import FeatureValidationResult


class FeatureSchemaValidator:
    """Validates feature vectors against registered schemas."""

    def validate_vector(
        self,
        vector: FeatureVector,
        *,
        schema: FeatureSchema,
    ) -> FeatureValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        present = {feature.name for feature in vector.features}
        missing = [name for name in schema.required_fields if name not in present]
        checks["required_fields_present"] = not missing
        if missing:
            errors.extend(f"Missing schema field: {name}" for name in missing)
        return FeatureValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_batch(
        self,
        vectors: tuple[FeatureVector, ...],
        *,
        schema: FeatureSchema,
    ) -> FeatureValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        for vector in vectors:
            result = self.validate_vector(vector, schema=schema)
            if not result.valid:
                errors.extend(result.errors)
        checks["all_vectors_valid"] = not errors
        return FeatureValidationResult(valid=not errors, checks=checks, errors=tuple(errors))
