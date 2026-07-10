"""Unit tests for pipeline executor."""

from __future__ import annotations

import pytest

from pipeline import (
    PipelineBuilder,
    PipelineExecutor,
    PipelineStatus,
    build_pipeline_context,
)
from services import reset_application_context
from tests.pipeline_fixtures import IngestStage, TransformStage
from tests.pipeline_helpers import make_pipeline_request


@pytest.fixture(autouse=True)
def _reset_context() -> None:
    reset_application_context()
    yield
    reset_application_context()


@pytest.mark.unit
def test_executor_runs_stages_in_dependency_order() -> None:
    context = build_pipeline_context()
    pipeline = (
        PipelineBuilder("exec-test").add_stage(TransformStage()).add_stage(IngestStage()).build()
    )
    executor = PipelineExecutor(context)
    response = executor.execute(pipeline, make_pipeline_request())
    assert response.result.status == PipelineStatus.COMPLETED
    assert [item.stage_name for item in response.result.stage_results] == [
        "ingest",
        "transform",
    ]


@pytest.mark.unit
def test_executor_records_metrics_and_timings() -> None:
    context = build_pipeline_context()
    pipeline = PipelineBuilder("metrics").add_stage(IngestStage()).build()
    executor = PipelineExecutor(context)
    response = executor.execute(pipeline, make_pipeline_request())
    assert "ingest" in response.result.timings
    assert response.result.metrics["pipeline.stage_count"] == 1


@pytest.mark.unit
def test_executor_rollback_on_stage_failure() -> None:
    context = build_pipeline_context()
    ingest = IngestStage()

    class _FailingTransform(TransformStage):
        def execute(self, context, request):
            msg = "transform failed"
            raise RuntimeError(msg)

    pipeline = PipelineBuilder("rollback").add_stage(ingest).add_stage(_FailingTransform()).build()
    executor = PipelineExecutor(context)
    response = executor.execute(pipeline, make_pipeline_request())
    assert response.result.status == PipelineStatus.FAILED
    assert ingest._rolled_back is True


@pytest.mark.unit
def test_executor_runs_hooks() -> None:
    context = build_pipeline_context()
    calls: list[str] = []
    pipeline = (
        PipelineBuilder("hooked")
        .add_stage(IngestStage())
        .add_pre_hook(lambda _c, _r, _s: calls.append("pre"))
        .add_post_hook(lambda _c, _r, _s: calls.append("post"))
        .add_before_stage_hook(lambda _c, _r, _s: calls.append("before"))
        .add_after_stage_hook(lambda _c, _r, _s, _res: calls.append("after"))
        .build()
    )
    executor = PipelineExecutor(context)
    executor.execute(pipeline, make_pipeline_request())
    assert calls == ["pre", "before", "after", "post"]
