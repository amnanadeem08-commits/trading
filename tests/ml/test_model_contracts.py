"""Unit tests for ML model contracts."""

from __future__ import annotations

import inspect

import pytest

from ml import MLModel
from tests.ml_helpers import SampleMLModel, make_model_metadata


@pytest.mark.unit
def test_ml_model_contract_methods() -> None:
    methods = {name for name, _ in inspect.getmembers(MLModel, predicate=inspect.isfunction)}
    assert "model_id" in methods
    assert "train" in methods
    assert "predict" in methods


@pytest.mark.unit
def test_sample_model_satisfies_contract() -> None:
    model = SampleMLModel()
    assert model.model_id() == "sample-model"
    assert model.metadata().framework == "platform"


@pytest.mark.unit
def test_model_artifact_defaults() -> None:
    artifact = SampleMLModel().artifact()
    assert artifact.model_id == "sample-model"
    assert artifact.uri == "memory://artifact"


@pytest.mark.unit
def test_model_metadata_fields() -> None:
    metadata = make_model_metadata()
    assert metadata.model_id == "sample-model"
    assert metadata.tags == ("test",)
