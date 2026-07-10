"""Training job specification."""

from __future__ import annotations

from typing import Any

from models.common import PlatformModel
from training_pipeline.datasets.dataset_reference import DatasetReference


class TrainingJobSpec(PlatformModel):
    """Specification for a training job. Infrastructure contract only."""

    job_id: str
    experiment_id: str
    model_family: str
    training_version: str
    dataset: DatasetReference
    hyperparameters: dict[str, Any]
    tags: tuple[str, ...] = ()
    correlation_id: str = ""
    trace_id: str = ""
