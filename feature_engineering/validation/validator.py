"""Feature validator."""

from __future__ import annotations

from feature_engineering.models.feature_batch import FeatureBatch
from feature_engineering.models.feature_set import FeatureSet
from feature_engineering.models.feature_vector import FeatureVector
from feature_engineering.validation.validation_result import FeatureValidationResult
from feature_engineering.validation.validation_rule import FeatureValidationRule


class FeatureValidator:
    """Validates feature vectors, batches, and sets."""

    def __init__(self, *, rules: tuple[FeatureValidationRule, ...] = ()) -> None:
        self._rules = rules

    @property
    def rules(self) -> tuple[FeatureValidationRule, ...]:
        return self._rules

    def validate_vector(self, vector: FeatureVector | None) -> FeatureValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        checks["vector_present"] = vector is not None
        if vector is None:
            errors.append("Feature vector is required")
            return FeatureValidationResult(valid=False, checks=checks, errors=tuple(errors))
        checks["vector_id_present"] = bool(vector.vector_id.strip())
        checks["dataset_id_present"] = bool(vector.dataset_id.strip())
        checks["symbol_id_present"] = bool(vector.symbol_id.strip())
        if not checks["vector_id_present"]:
            errors.append("Vector id is required")
        for rule in self._rules:
            result = rule.validate(vector)
            checks[rule.rule_id] = result.valid
            errors.extend(result.errors)
        return FeatureValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_batch(self, batch: FeatureBatch) -> FeatureValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        seen: set[str] = set()
        duplicate = False
        for vector in batch.vectors:
            if vector.vector_id in seen:
                duplicate = True
                break
            seen.add(vector.vector_id)
            result = self.validate_vector(vector)
            if not result.valid:
                errors.extend(result.errors)
        checks["no_duplicates"] = not duplicate
        if duplicate:
            errors.append("Duplicate vector ids detected")
        return FeatureValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_set(self, feature_set: FeatureSet) -> FeatureValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        checks["metadata_present"] = feature_set.metadata is not None
        checks["vectors_present"] = len(feature_set.vectors) > 0
        if not checks["vectors_present"]:
            errors.append("Feature set must contain vectors")
        batch = FeatureBatch(
            batch_id=feature_set.feature_set_id,
            pipeline_id=feature_set.feature_set_id,
            dataset_id=feature_set.metadata.dataset_id,
            symbol_id=feature_set.metadata.symbol_id,
            vectors=feature_set.vectors,
        )
        batch_result = self.validate_batch(batch)
        checks.update(batch_result.checks)
        errors.extend(batch_result.errors)
        return FeatureValidationResult(valid=not errors, checks=checks, errors=tuple(errors))
