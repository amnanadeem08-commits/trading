"""Unit tests for training metrics."""

from __future__ import annotations

import pytest

from training_pipeline import TrainingJobStatus, TrainingMetricsCollector, TrainingSummary


@pytest.mark.unit
def test_metrics_collector_statistics() -> None:
    collector = TrainingMetricsCollector()
    collector.record_status(TrainingJobStatus.QUEUED)
    collector.record_status(TrainingJobStatus.COMPLETED)
    collector.record_artifact()
    collector.record_checkpoint()
    stats = collector.statistics()
    assert stats.total_jobs == 2
    assert stats.completed_jobs == 1
    assert stats.total_artifacts == 1
    assert stats.total_checkpoints == 1


@pytest.mark.unit
def test_metrics_collector_summary() -> None:
    collector = TrainingMetricsCollector()
    collector.record_summary(
        TrainingSummary(
            job_id="job-1",
            experiment_id="exp-1",
            status=TrainingJobStatus.COMPLETED,
            artifact_stored=True,
        )
    )
    summary = collector.get_summary("job-1")
    assert summary is not None
    assert summary.artifact_stored is True
