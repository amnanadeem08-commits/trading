"""Unit tests for dispatch queue."""

from __future__ import annotations

import pytest

from execution import DispatchQueue
from execution.dispatch.dispatcher import Dispatcher
from execution.exceptions import QueueError
from tests.execution_helpers import make_execution_context


def test_queue_enqueue_dequeue() -> None:
    queue = DispatchQueue()
    dispatcher = Dispatcher(queue=queue)
    context = make_execution_context()
    request = dispatcher.create_request(
        execution_id="exec-1",
        engine_id="sample-engine",
        context=context,
    )
    queue.enqueue(request)
    assert queue.size() == 1
    dequeued = queue.dequeue()
    assert dequeued.execution_id == "exec-1"
    assert queue.size() == 0


def test_queue_priority_ordering() -> None:
    queue = DispatchQueue()
    dispatcher = Dispatcher(queue=queue)
    context = make_execution_context()
    low = dispatcher.create_request(
        execution_id="exec-low",
        engine_id="sample-engine",
        context=context,
        priority=0,
    )
    high = dispatcher.create_request(
        execution_id="exec-high",
        engine_id="sample-engine",
        context=context,
        priority=10,
    )
    queue.enqueue(low)
    queue.enqueue(high)
    first = queue.dequeue()
    assert first.execution_id == "exec-high"


def test_queue_peek() -> None:
    queue = DispatchQueue()
    dispatcher = Dispatcher(queue=queue)
    context = make_execution_context()
    request = dispatcher.create_request(
        execution_id="exec-1",
        engine_id="sample-engine",
        context=context,
    )
    queue.enqueue(request)
    peeked = queue.peek()
    assert peeked is not None
    assert peeked.execution_id == "exec-1"
    assert queue.size() == 1


def test_queue_empty_dequeue_raises() -> None:
    queue = DispatchQueue()
    with pytest.raises(QueueError):
        queue.dequeue()


def test_queue_clear_and_list() -> None:
    queue = DispatchQueue()
    dispatcher = Dispatcher(queue=queue)
    context = make_execution_context()
    request = dispatcher.create_request(
        execution_id="exec-1",
        engine_id="sample-engine",
        context=context,
    )
    queue.enqueue(request)
    assert len(queue.list_all()) == 1
    queue.clear()
    assert queue.size() == 0
