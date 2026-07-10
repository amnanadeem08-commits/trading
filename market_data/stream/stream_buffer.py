"""In-memory stream buffer."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from market_data.exceptions import StreamError
from market_data.models.market_record import MarketRecord
from market_data.stream.stream_batch import StreamBatch
from market_data.stream.stream_context import StreamContext
from market_data.stream.stream_result import StreamResult


class StreamBuffer:
    """Buffers market records with cursor, offset, window, and pagination."""

    def __init__(self, context: StreamContext, records: tuple[MarketRecord, ...] = ()) -> None:
        self._context = context
        self._records = records
        self._lock = RLock()
        self._position = context.offset

    @property
    def context(self) -> StreamContext:
        return self._context

    @property
    def position(self) -> int:
        with self._lock:
            return self._position

    @property
    def total(self) -> int:
        return len(self._records)

    def append(self, record: MarketRecord) -> None:
        with self._lock:
            if len(self._records) >= self._context.buffer_size:
                msg = "Stream buffer capacity exceeded"
                raise StreamError(msg)
            self._records = (*self._records, record)

    def next(self) -> StreamResult | None:
        with self._lock:
            if self._position >= len(self._records):
                return StreamResult(
                    stream_id=self._context.stream_id,
                    offset=self._context.offset,
                    position=self._position,
                    total=len(self._records),
                    completed=True,
                )
            record = self._records[self._position]
            self._position += 1
            completed = self._position >= len(self._records)
            return StreamResult(
                stream_id=self._context.stream_id,
                offset=self._context.offset,
                position=self._position,
                total=len(self._records),
                record=record,
                completed=completed,
            )

    def seek(self, position: int) -> int:
        with self._lock:
            if position < 0 or position > len(self._records):
                msg = f"Invalid stream position: {position}"
                raise StreamError(msg)
            self._position = position
            return self._position

    def window(self, *, size: int | None = None) -> tuple[MarketRecord, ...]:
        with self._lock:
            window_size = size or self._context.window_size
            end = min(self._position + window_size, len(self._records))
            return self._records[self._position : end]

    def page(self, *, page: int, page_size: int | None = None) -> StreamBatch:
        with self._lock:
            size = page_size or self._context.batch_size
            start = page * size
            if start >= len(self._records):
                return StreamBatch(
                    stream_id=self._context.stream_id,
                    batch_id=str(uuid4()),
                    offset=start,
                    records=(),
                    total=len(self._records),
                    completed=True,
                )
            end = min(start + size, len(self._records))
            batch_records = self._records[start:end]
            return StreamBatch(
                stream_id=self._context.stream_id,
                batch_id=str(uuid4()),
                offset=start,
                records=batch_records,
                total=len(self._records),
                completed=end >= len(self._records),
            )

    def reset(self) -> None:
        with self._lock:
            self._position = self._context.offset
