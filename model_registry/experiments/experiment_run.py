"""Experiment run contract."""

from __future__ import annotations

from typing import Any

from model_registry.experiments.experiment_metrics import ExperimentMetrics
from models.common import PlatformModel, UTCDateTime


class ExperimentRun(PlatformModel):
    """Tracked experiment run from the training pipeline."""

    run_id: str
    experiment_id: str
    job_id: str
    artifact_id: str
    dataset_id: str
    dataset_snapshot_id: str | None = None
    parameters: dict[str, Any]
    metrics: ExperimentMetrics | None = None
    config_hash: str = ""
    checksum: str = ""
    started_at: UTCDateTime
    completed_at: UTCDateTime
