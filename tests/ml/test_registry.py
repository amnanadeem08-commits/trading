"""Unit tests for ML registry."""

from __future__ import annotations

import pytest

from ml import (
    MLRegistry,
    MLRegistryError,
    ModelLifecycleState,
    ModelNotFoundError,
    ModelRegistrationError,
    ModelRegistry,
    get_ml_registry,
    reset_ml_registry,
)
from ml.training.training_job import TrainingJob, TrainingJobState
from tests.ml_helpers import SampleMLModel, make_model_metadata


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_ml_registry()
    yield
    reset_ml_registry()


@pytest.mark.unit
def test_model_registry_register_and_resolve() -> None:
    registry = ModelRegistry()
    metadata = make_model_metadata()
    registry.register_metadata(metadata)
    resolved = registry.resolve_metadata("sample-model")
    assert resolved.name == "Sample Model"
    assert registry.list() == ("sample-model",)


@pytest.mark.unit
def test_model_registry_register_type() -> None:
    registry = ModelRegistry()
    registry.register_type(SampleMLModel)
    model_type = registry.resolve_type("sample-model")
    assert model_type is SampleMLModel


@pytest.mark.unit
def test_model_registry_duplicate_raises() -> None:
    registry = ModelRegistry()
    registry.register_metadata(make_model_metadata())
    with pytest.raises(ModelRegistrationError):
        registry.register_metadata(make_model_metadata())


@pytest.mark.unit
def test_ml_registry_lifecycle_tracking() -> None:
    ml_registry = MLRegistry()
    metadata = make_model_metadata()
    ml_registry.register_model(metadata)
    assert ml_registry.get_state("sample-model") == ModelLifecycleState.REGISTERED
    job = TrainingJob(
        job_id="job-1",
        model_id="sample-model",
        dataset_id="records",
        state=TrainingJobState.RUNNING,
    )
    ml_registry.track_job(job)
    assert ml_registry.get_state("sample-model") == ModelLifecycleState.TRAINING


@pytest.mark.unit
def test_ml_registry_get_job_missing_raises() -> None:
    ml_registry = MLRegistry()
    with pytest.raises(MLRegistryError):
        ml_registry.get_job("missing")


@pytest.mark.unit
def test_ml_registry_get_model_missing_raises() -> None:
    ml_registry = MLRegistry()
    with pytest.raises(ModelNotFoundError):
        ml_registry.get_model("missing")


@pytest.mark.unit
def test_get_ml_registry_singleton() -> None:
    first = get_ml_registry()
    second = get_ml_registry()
    assert first is second
