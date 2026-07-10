"""Feature validation rule contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from feature_engineering.models.feature_vector import FeatureVector
from feature_engineering.validation.validation_result import FeatureValidationResult


class FeatureValidationRule(ABC):
    """Base contract for feature validation rules."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Return the rule identifier."""

    @abstractmethod
    def validate(self, vector: FeatureVector) -> FeatureValidationResult:
        """Validate a feature vector against this rule."""


class RequiredFieldsRule(FeatureValidationRule):
    """Ensures required feature names are present."""

    def __init__(self, *, required_fields: tuple[str, ...]) -> None:
        self._required_fields = required_fields

    @property
    def rule_id(self) -> str:
        return "required_fields"

    def validate(self, vector: FeatureVector) -> FeatureValidationResult:
        present = {feature.name for feature in vector.features}
        missing = [name for name in self._required_fields if name not in present]
        checks = {"all_required_present": not missing}
        errors = [f"Missing required feature: {name}" for name in missing]
        return FeatureValidationResult(valid=not errors, checks=checks, errors=tuple(errors))


class NonEmptyVectorRule(FeatureValidationRule):
    """Ensures a feature vector contains at least one feature."""

    @property
    def rule_id(self) -> str:
        return "non_empty_vector"

    def validate(self, vector: FeatureVector) -> FeatureValidationResult:
        has_features = len(vector.features) > 0
        checks = {"has_features": has_features}
        errors = () if has_features else ("Feature vector is empty",)
        return FeatureValidationResult(valid=has_features, checks=checks, errors=errors)
