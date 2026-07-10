"""Contract tests for workflow layer."""

from __future__ import annotations

import pytest

from tests.workflow_helpers import make_single_job_workflow
from workflow import Job, JobState, WorkflowResult, WorkflowStatus


@pytest.mark.contract
def test_workflow_contract_fields() -> None:
    workflow = make_single_job_workflow()
    assert workflow.workflow_id == "wf-single"
    assert workflow.version == "1.0.0"
    assert len(workflow.jobs) == 1
    assert workflow.metadata == {}


@pytest.mark.contract
def test_job_contract_fields() -> None:
    job = Job(job_id="job-1", pipeline_name="ingest-pipeline", priority=5)
    assert job.job_id == "job-1"
    assert job.pipeline_name == "ingest-pipeline"
    assert job.priority == 5
    assert job.dependencies == ()
    assert job.timeout_seconds >= 1


@pytest.mark.contract
def test_workflow_result_contract_fields() -> None:
    result = WorkflowResult(
        workflow_id="wf-1",
        status=WorkflowStatus.COMPLETED,
        completed_jobs=("job-1",),
        failed_jobs=(),
        cancelled_jobs=(),
        metrics={},
        timings={},
    )
    assert result.status == WorkflowStatus.COMPLETED
    assert result.completed_jobs == ("job-1",)


@pytest.mark.contract
def test_job_state_values() -> None:
    assert JobState.CREATED.value == "created"
    assert JobState.TIMED_OUT.value == "timed_out"
