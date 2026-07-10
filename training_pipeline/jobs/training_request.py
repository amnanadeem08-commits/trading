"""Training request contract."""

from __future__ import annotations

from typing import Any

from models.common import PlatformModel
from training_pipeline.datasets.dataset_reference import DatasetReference


class TrainingRequest(PlatformModel):
    """Request to schedule a training job."""

    request_id: str
    experiment_id: str
    model_family: str
    dataset: DatasetReference
    hyperparameters: dict[str, Any]
    training_version: str = "1.0.0"
    priority: int = 0
    tags: tuple[str, ...] = ()
    correlation_id: str = ""
    trace_id: str = ""
