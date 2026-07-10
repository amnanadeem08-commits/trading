"""Unit tests for artifact store."""

from __future__ import annotations

import pytest

from tests.training_pipeline_helpers import make_dataset_reference
from training_pipeline import ArtifactNotFoundError, ArtifactStore


@pytest.mark.unit
def test_artifact_store_round_trip() -> None:
    store = ArtifactStore()
    artifact = store.store(
        experiment_id="exp-1",
        run_id="run-1",
        job_id="job-1",
        model_family="baseline",
        training_version="1.0.0",
        dataset=make_dataset_reference(),
        hyperparameters={"epochs": 1},
    )
    loaded = store.get(artifact.artifact_id)
    assert loaded.metadata.job_id == "job-1"
    assert loaded.manifest.reproducibility_key


@pytest.mark.unit
def test_artifact_store_missing_raises() -> None:
    store = ArtifactStore()
    with pytest.raises(ArtifactNotFoundError):
        store.get("missing")
