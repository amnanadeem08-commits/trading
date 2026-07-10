"""Unit tests for dispatcher."""

from __future__ import annotations

import pytest

from execution import Dispatcher, DispatchError
from tests.execution_helpers import make_execution_context


def test_dispatcher_create_request() -> None:
    dispatcher = Dispatcher()
    context = make_execution_context()
    request = dispatcher.create_request(
        execution_id="exec-1",
        engine_id="sample-engine",
        context=context,
        payload={"key": "value"},
        priority=1,
    )
    assert request.execution_id == "exec-1"
    assert request.priority == 1


def test_dispatcher_enqueue_and_dispatch() -> None:
    dispatcher = Dispatcher()
    context = make_execution_context()
    request = dispatcher.create_request(
        execution_id="exec-1",
        engine_id="sample-engine",
        context=context,
    )
    dispatcher.enqueue(request)
    result = dispatcher.dispatch(request)
    assert result.success is True
    assert result.output["status"] == "recorded"


def test_dispatcher_dispatch_next() -> None:
    dispatcher = Dispatcher()
    context = make_execution_context()
    request = dispatcher.create_request(
        execution_id="exec-1",
        engine_id="sample-engine",
        context=context,
    )
    dispatcher.enqueue(request)
    result = dispatcher.dispatch_next()
    assert result.execution_id == "exec-1"


def test_dispatcher_dispatch_next_empty_raises() -> None:
    dispatcher = Dispatcher()
    with pytest.raises(DispatchError):
        dispatcher.dispatch_next()


def test_dispatcher_history() -> None:
    dispatcher = Dispatcher()
    context = make_execution_context()
    request = dispatcher.create_request(
        execution_id="exec-1",
        engine_id="sample-engine",
        context=context,
    )
    dispatcher.dispatch(request)
    assert len(dispatcher.history()) == 1


def test_dispatcher_reset() -> None:
    dispatcher = Dispatcher()
    context = make_execution_context()
    request = dispatcher.create_request(
        execution_id="exec-1",
        engine_id="sample-engine",
        context=context,
    )
    dispatcher.enqueue(request)
    dispatcher.dispatch(request)
    dispatcher.reset()
    assert dispatcher.queue.size() == 0
    assert dispatcher.history() == []
