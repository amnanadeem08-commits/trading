"""Unit tests for registry validation."""

from __future__ import annotations

import pytest

from model_registry import ModelRegistry, ModelStage, RegistryValidator
from tests.model_registry_helpers import make_registered_model


@pytest.mark.unit
def test_validate_model_success() -> None:
    validator = RegistryValidator()
    result = validator.validate_model(make_registered_model())
    assert result.valid is True


@pytest.mark.unit
def test_validate_model_failure() -> None:
    validator = RegistryValidator()
    model = make_registered_model(model_id="")
    result = validator.validate_model(model)
    assert result.valid is False


@pytest.mark.unit
def test_validate_promotion_invalid_transition() -> None:
    registry = ModelRegistry()
    registry.register_model(make_registered_model())
    version = registry.build_version(
        model_id="model-1",
        semantic_version="1.0.0",
        artifact_id="artifact-1",
        dataset_id="dataset-1",
        experiment_id="exp-1",
        run_id="run-1",
        job_id="job-1",
        config_hash="hash",
        checksum="checksum-1",
        stage=ModelStage.DRAFT,
    )
    validator = RegistryValidator()
    result = validator.validate_promotion(version=version, to_stage=ModelStage.PRODUCTION)
    assert result.valid is False
