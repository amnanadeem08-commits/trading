"""Experiment metadata and run contracts."""

from __future__ import annotations

from typing import Any

from models.common import PlatformModel, UTCDateTime, utc_now
from training_pipeline.datasets.dataset_reference import DatasetReference
from training_pipeline.jobs.training_job_status import TrainingJobStatus


class ExperimentMetadata(PlatformModel):
    """Metadata describing an experiment."""

    experiment_id: str
    name: str
    description: str = ""
    owner: str = "platform"
    tags: tuple[str, ...] = ()
    created_at: UTCDateTime


class Experiment(PlatformModel):
    """Experiment definition for grouped training runs."""

    metadata: ExperimentMetadata
    model_family: str
    default_hyperparameters: dict[str, Any]
    dataset: DatasetReference | None = None

    @classmethod
    def create(
        cls,
        *,
        experiment_id: str,
        name: str,
        model_family: str,
        default_hyperparameters: dict[str, Any] | None = None,
        description: str = "",
        tags: tuple[str, ...] = (),
    ) -> Experiment:
        metadata = ExperimentMetadata(
            experiment_id=experiment_id,
            name=name,
            description=description,
            tags=tags,
            created_at=utc_now(),
        )
        return cls(
            metadata=metadata,
            model_family=model_family,
            default_hyperparameters=default_hyperparameters or {},
        )

    @property
    def experiment_id(self) -> str:
        return self.metadata.experiment_id


class ExperimentRun(PlatformModel):
    """Single execution of an experiment."""

    run_id: str
    experiment_id: str
    job_id: str
    status: TrainingJobStatus
    dataset: DatasetReference
    hyperparameters: dict[str, Any]
    artifact_id: str | None = None
    checkpoint_id: str | None = None
    started_at: UTCDateTime
    completed_at: UTCDateTime | None = None
