"""Unit tests for market data streaming."""

from __future__ import annotations

import pytest

from market_data import StreamBuffer
from market_data.exceptions import StreamError
from tests.market_data_helpers import make_sample_market_record, make_stream_context


@pytest.mark.unit
def test_stream_buffer_next_and_complete() -> None:
    records = tuple(
        make_sample_market_record(record_id=f"record-{index}", sequence=index) for index in range(3)
    )
    buffer = StreamBuffer(make_stream_context(), records)
    first = buffer.next()
    assert first is not None
    assert first.record is not None
    assert first.record.record_id == "record-0"
    assert first.completed is False


@pytest.mark.unit
def test_stream_buffer_seek_and_window() -> None:
    records = tuple(
        make_sample_market_record(record_id=f"record-{index}", sequence=index) for index in range(3)
    )
    context = make_stream_context()
    context = context.model_copy(update={"window_size": 2})
    buffer = StreamBuffer(context, records)
    buffer.seek(1)
    window = buffer.window()
    assert len(window) == 2
    assert window[0].record_id == "record-1"


@pytest.mark.unit
def test_stream_buffer_page() -> None:
    records = tuple(
        make_sample_market_record(record_id=f"record-{index}", sequence=index) for index in range(5)
    )
    context = make_stream_context(batch_size=2)
    buffer = StreamBuffer(context, records)
    page = buffer.page(page=0)
    assert len(page.records) == 2
    assert page.offset == 0
    last_page = buffer.page(page=2)
    assert last_page.completed is True


@pytest.mark.unit
def test_stream_buffer_append_and_capacity() -> None:
    context = make_stream_context(buffer_size=2)
    buffer = StreamBuffer(context)
    buffer.append(make_sample_market_record(record_id="record-1"))
    buffer.append(make_sample_market_record(record_id="record-2"))
    with pytest.raises(StreamError):
        buffer.append(make_sample_market_record(record_id="record-3"))


@pytest.mark.unit
def test_stream_buffer_reset() -> None:
    records = (make_sample_market_record(record_id="record-1"),)
    buffer = StreamBuffer(make_stream_context(), records)
    buffer.next()
    buffer.reset()
    assert buffer.position == 0


@pytest.mark.unit
def test_stream_buffer_seek_invalid_position() -> None:
    buffer = StreamBuffer(make_stream_context())
    with pytest.raises(StreamError):
        buffer.seek(5)
