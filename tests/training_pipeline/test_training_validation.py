"""Unit tests for training validation."""

from __future__ import annotations

import pytest

from tests.training_pipeline_helpers import make_training_job_spec, make_training_request
from training_pipeline import TrainingValidator


@pytest.mark.unit
def test_validate_request_success() -> None:
    validator = TrainingValidator()
    result = validator.validate_request(make_training_request())
    assert result.valid is True


@pytest.mark.unit
def test_validate_request_failure() -> None:
    validator = TrainingValidator()
    request = make_training_request().model_copy(update={"experiment_id": ""})
    result = validator.validate_request(request)
    assert result.valid is False
    assert result.errors


@pytest.mark.unit
def test_validate_spec_success() -> None:
    validator = TrainingValidator()
    result = validator.validate_spec(make_training_job_spec())
    assert result.valid is True
