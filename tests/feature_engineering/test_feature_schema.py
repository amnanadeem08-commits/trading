"""Unit tests for feature schema."""

from __future__ import annotations

import pytest

from feature_engineering import FeatureSchemaRegistry, FeatureSchemaValidator
from feature_engineering.exceptions import FeatureSchemaError
from tests.feature_engineering_helpers import make_feature_schema, make_sample_feature_vector


@pytest.mark.unit
def test_schema_registry_register_and_lookup() -> None:
    registry = FeatureSchemaRegistry()
    schema = make_feature_schema()
    registry.register(schema)
    resolved = registry.lookup("feature-schema-v1")
    assert resolved.name == "Sample Feature Schema"
    assert registry.exists("feature-schema-v1") is True


@pytest.mark.unit
def test_schema_registry_missing_raises() -> None:
    registry = FeatureSchemaRegistry()
    with pytest.raises(FeatureSchemaError):
        registry.lookup("missing")


@pytest.mark.unit
def test_schema_validator_required_fields() -> None:
    validator = FeatureSchemaValidator()
    schema = make_feature_schema(required_fields=("close", "volume"))
    vector = make_sample_feature_vector()
    result = validator.validate_vector(vector, schema=schema)
    assert result.valid is True


@pytest.mark.unit
def test_schema_validator_missing_fields() -> None:
    validator = FeatureSchemaValidator()
    schema = make_feature_schema(required_fields=("close", "volume", "open"))
    vector = make_sample_feature_vector()
    result = validator.validate_vector(vector, schema=schema)
    assert result.valid is False
    assert "Missing schema field: open" in result.errors


@pytest.mark.unit
def test_schema_validator_batch() -> None:
    validator = FeatureSchemaValidator()
    schema = make_feature_schema()
    vectors = (make_sample_feature_vector(), make_sample_feature_vector(vector_id="vector-2"))
    result = validator.validate_batch(vectors, schema=schema)
    assert result.valid is True
