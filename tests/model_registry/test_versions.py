"""Unit tests for model versions."""

from __future__ import annotations

import pytest

from model_registry import ModelRegistry, ModelVersionNotFoundError, RegistryValidationError
from tests.model_registry_helpers import make_registered_model, seed_trained_model


@pytest.mark.unit
def test_register_and_latest_version() -> None:
    runtime = seed_trained_model()
    latest = runtime.registry.latest("model-1")
    assert latest.model_id == "model-1"
    assert latest.artifact_id


@pytest.mark.unit
def test_versions_list() -> None:
    runtime = seed_trained_model()
    versions = runtime.registry.versions("model-1")
    assert len(versions) == 1


@pytest.mark.unit
def test_duplicate_checksum_rejected() -> None:
    registry = ModelRegistry()
    registry.register_model(make_registered_model())
    first = registry.build_version(
        model_id="model-1",
        semantic_version="1.0.0",
        artifact_id="artifact-1",
        dataset_id="dataset-1",
        experiment_id="exp-1",
        run_id="run-1",
        job_id="job-1",
        config_hash="hash-1",
        checksum="same-checksum",
    )
    registry.register_version(first)
    duplicate = first.model_copy(
        update={"version_id": registry.new_version_id(), "semantic_version": "1.0.1"}
    )
    with pytest.raises(RegistryValidationError):
        registry.register_version(duplicate)


@pytest.mark.unit
def test_latest_without_versions_raises() -> None:
    registry = ModelRegistry()
    registry.register_model(make_registered_model())
    with pytest.raises(ModelVersionNotFoundError):
        registry.latest("model-1")
