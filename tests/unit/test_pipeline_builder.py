"""Unit tests for pipeline builder."""

from __future__ import annotations

import pytest

from pipeline import PipelineBuilder
from tests.pipeline_fixtures import IngestStage, TransformStage


@pytest.mark.unit
def test_builder_add_and_remove_stages() -> None:
    builder = PipelineBuilder("test-pipeline")
    builder.add_stage(IngestStage()).add_stage(TransformStage())
    pipeline = builder.build()
    assert set(pipeline.stages.keys()) == {"ingest", "transform"}
    builder.remove_stage("transform")
    pipeline = builder.build()
    assert list(pipeline.stages.keys()) == ["ingest"]


@pytest.mark.unit
def test_builder_duplicate_stage_raises() -> None:
    builder = PipelineBuilder("test-pipeline")
    builder.add_stage(IngestStage())
    with pytest.raises(ValueError, match="Duplicate stage"):
        builder.add_stage(IngestStage())


@pytest.mark.unit
def test_builder_hooks_and_retry_policy() -> None:
    pre_called: list[str] = []
    post_called: list[str] = []
    before_called: list[str] = []
    after_called: list[str] = []

    class _Policy:
        def should_retry(self, *, attempt: int, error: Exception) -> bool:
            return False

        def max_attempts(self) -> int:
            return 1

    builder = (
        PipelineBuilder("hooks")
        .add_stage(IngestStage())
        .add_pre_hook(lambda _c, _r, stage: pre_called.append(stage.name()))
        .add_post_hook(lambda _c, _r, stage: post_called.append(stage.name()))
        .add_before_stage_hook(lambda _c, _r, stage: before_called.append(stage.name()))
        .add_after_stage_hook(lambda _c, _r, stage, _result: after_called.append(stage.name()))
        .with_retry_policy(_Policy())
    )
    pipeline = builder.build()
    assert pipeline.retry_policy is not None
    assert pipeline.pre_hooks
    assert pipeline.post_hooks
