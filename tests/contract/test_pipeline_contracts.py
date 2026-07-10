"""Contract tests for pipeline layer."""

from __future__ import annotations

import pytest

from pipeline import PipelineResult, PipelineStage, PipelineStatus, StageResult, StageStatus
from pipeline.context import build_pipeline_context
from tests.pipeline_fixtures import IngestStage, TransformStage
from tests.pipeline_helpers import make_pipeline_request


@pytest.mark.contract
def test_pipeline_stage_contract_methods() -> None:
    required = {
        "name",
        "version",
        "dependencies",
        "validate",
        "execute",
        "rollback",
        "cleanup",
    }
    assert required.issubset(set(dir(PipelineStage)))
    for method_name in required:
        assert getattr(PipelineStage, method_name) is not None


@pytest.mark.contract
@pytest.mark.parametrize("stage_type", [IngestStage, TransformStage])
def test_stage_implementations_satisfy_contract(stage_type: type[PipelineStage]) -> None:
    stage = stage_type()
    assert isinstance(stage.name(), str)
    assert isinstance(stage.version(), str)
    assert isinstance(stage.dependencies(), tuple)
    context = build_pipeline_context()
    request = make_pipeline_request()
    stage.validate(context, request)
    result = stage.execute(context, request)
    assert isinstance(result, StageResult)
    stage.rollback(context, request)
    stage.cleanup(context, request)


@pytest.mark.contract
def test_pipeline_result_contract_fields() -> None:
    result = PipelineResult(
        pipeline_name="test",
        status=PipelineStatus.COMPLETED,
        errors=(),
        warnings=(),
        metrics={},
        timings={},
        stage_results=(),
    )
    assert result.pipeline_name == "test"
    assert result.status == PipelineStatus.COMPLETED
    assert result.errors == ()
    assert result.stage_results == ()


@pytest.mark.contract
def test_stage_result_status_values() -> None:
    assert StageStatus.COMPLETED.value == "completed"
    assert StageStatus.SKIPPED.value == "skipped"
