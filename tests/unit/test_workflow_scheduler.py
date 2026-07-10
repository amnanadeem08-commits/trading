"""Unit tests for workflow scheduler."""

from __future__ import annotations

import pytest

from tests.workflow_helpers import make_single_job_workflow
from workflow import InMemoryWorkflowScheduler


@pytest.mark.unit
def test_scheduler_schedule_pause_resume_cancel() -> None:
    scheduler = InMemoryWorkflowScheduler()
    handle = scheduler.schedule(make_single_job_workflow())
    assert handle.workflow_id == "wf-single"
    scheduler.pause(handle.schedule_id)
    assert scheduler.is_paused(handle.schedule_id) is True
    scheduler.resume(handle.schedule_id)
    assert scheduler.is_paused(handle.schedule_id) is False
    scheduler.cancel(handle.schedule_id)
    assert scheduler.list_schedules() == ()
