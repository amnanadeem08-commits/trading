"""Experiment summary contract."""

from __future__ import annotations

from model_registry.experiments.experiment_metrics import ExperimentMetrics
from model_registry.models.model_stage import ModelStage
from models.common import PlatformModel, UTCDateTime


class ExperimentSummary(PlatformModel):
    """Summary of an experiment run for registry indexing."""

    run_id: str
    experiment_id: str
    model_id: str | None = None
    version_id: str | None = None
    artifact_id: str
    dataset_id: str
    stage: ModelStage = ModelStage.DRAFT
    metrics: ExperimentMetrics | None = None
    completed_at: UTCDateTime
