"""Unit tests for workflow queue."""

from __future__ import annotations

import pytest

from workflow import InMemoryJobQueue, Job


@pytest.mark.unit
def test_queue_fifo_with_priority() -> None:
    queue = InMemoryJobQueue()
    queue.enqueue(Job(job_id="low", pipeline_name="p1", priority=1))
    queue.enqueue(Job(job_id="high", pipeline_name="p2", priority=10))
    first = queue.dequeue()
    assert first is not None
    assert first.job_id == "high"
    second = queue.dequeue()
    assert second is not None
    assert second.job_id == "low"
    assert queue.dequeue() is None


@pytest.mark.unit
def test_queue_peek_and_clear() -> None:
    queue = InMemoryJobQueue()
    queue.enqueue(Job(job_id="a", pipeline_name="p"))
    assert queue.peek() is not None
    assert queue.size() == 1
    queue.clear()
    assert queue.size() == 0
