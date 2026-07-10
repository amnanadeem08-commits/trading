"""Immutable experiment snapshot."""

from __future__ import annotations

from typing import Any

from model_registry.experiments.experiment_metrics import ExperimentMetrics
from models.common import PlatformModel, UTCDateTime


class ExperimentSnapshot(PlatformModel):
    """Frozen immutable record of an experiment run."""

    snapshot_id: str
    run_id: str
    experiment_id: str
    artifact_id: str
    dataset_id: str
    parameters: dict[str, Any]
    metrics: ExperimentMetrics | None = None
    config_hash: str
    checksum: str
    captured_at: UTCDateTime
    immutable: bool = True
