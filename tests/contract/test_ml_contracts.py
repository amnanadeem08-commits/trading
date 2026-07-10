"""Contract tests for ML layer."""

from __future__ import annotations

import inspect

import pytest

from ml import (
    EvaluationResult,
    FeatureSet,
    InferenceContext,
    MLModel,
    PredictionResult,
    TrainingJob,
    TrainingResult,
)
from tests.ml_helpers import SampleMLModel


@pytest.mark.contract
def test_ml_model_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(MLModel, predicate=inspect.isfunction)}
    assert "train" in methods
    assert "predict" in methods
    assert "evaluate" in methods


@pytest.mark.contract
def test_sample_model_contract_compliance() -> None:
    model = SampleMLModel()
    training = model.train(dataset_id="records", parameters={})
    assert isinstance(training, TrainingResult)
    prediction = model.predict(inputs=({"id": "1"},))
    assert isinstance(prediction, PredictionResult)
    evaluation = model.evaluate(dataset_id="records", predictions=({"score": 0.9},))
    assert isinstance(evaluation, EvaluationResult)


@pytest.mark.contract
def test_training_job_fields() -> None:
    job = TrainingJob(job_id="job-1", model_id="sample-model", dataset_id="records")
    assert job.job_id == "job-1"
    assert job.state.value == "created"


@pytest.mark.contract
def test_inference_context_fields() -> None:
    context = InferenceContext(
        inference_id="inf-1",
        model_id="sample-model",
        model_version="1.0.0",
    )
    assert context.input_count == 0


@pytest.mark.contract
def test_feature_set_fields() -> None:
    from ml import FeatureMetadata

    feature_metadata = FeatureMetadata(
        feature_set_id="features",
        name="Features",
        version="1.0.0",
        source_dataset_id="records",
    )
    feature_set = FeatureSet(feature_set_id="features", metadata=feature_metadata)
    assert feature_set.records == ()
