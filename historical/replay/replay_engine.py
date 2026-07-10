"""Historical replay engine."""

from __future__ import annotations

from threading import RLock

from historical.exceptions import ReplayError
from historical.replay.replay_context import ReplayContext
from historical.replay.replay_cursor import ReplayCursor, ReplayState
from historical.replay.replay_result import ReplayResult
from historical.storage.repository import Repository
from historical.storage.repository_record import RepositoryRecord
from models.common import UTCDateTime


class ReplayEngine:
    """Deterministic replay engine for historical records."""

    def __init__(self, repository: Repository) -> None:
        self._repository = repository
        self._lock = RLock()
        self._context: ReplayContext | None = None
        self._records: tuple[RepositoryRecord, ...] = ()
        self._cursor = ReplayCursor(position=0, total=0)
        self._state = ReplayState.READY

    @property
    def cursor(self) -> ReplayCursor:
        with self._lock:
            return self._cursor

    @property
    def state(self) -> ReplayState:
        with self._lock:
            return self._state

    def begin(self, context: ReplayContext) -> ReplayCursor:
        """Start a replay session from the beginning or a timestamp."""
        records = self._repository.load(context.dataset_id, version=context.version)
        if context.start_timestamp is not None:
            records = tuple(
                record for record in records if record.timestamp >= context.start_timestamp
            )
        if context.end_timestamp is not None:
            records = tuple(
                record for record in records if record.timestamp <= context.end_timestamp
            )
        with self._lock:
            self._context = context
            self._records = records
            self._state = ReplayState.RUNNING
            self._cursor = ReplayCursor(
                dataset_id=context.dataset_id,
                version=context.version,
                position=0,
                total=len(records),
                state=ReplayState.RUNNING,
                current_timestamp=records[0].timestamp if records else None,
            )
            return self._cursor

    def next(self) -> ReplayResult | None:
        """Advance replay by one record."""
        with self._lock:
            if self._state not in {ReplayState.RUNNING, ReplayState.READY}:
                return None
            if self._cursor.position >= self._cursor.total:
                self._state = ReplayState.COMPLETED
                return ReplayResult(
                    dataset_id=self._cursor.dataset_id,
                    version=self._cursor.version,
                    position=self._cursor.position,
                    total=self._cursor.total,
                    state=ReplayState.COMPLETED,
                    completed=True,
                )
            record = self._records[self._cursor.position]
            position = self._cursor.position + 1
            completed = position >= self._cursor.total
            self._cursor = self._cursor.model_copy(
                update={
                    "position": position,
                    "current_timestamp": record.timestamp,
                    "state": ReplayState.COMPLETED if completed else ReplayState.RUNNING,
                }
            )
            if completed:
                self._state = ReplayState.COMPLETED
            return ReplayResult(
                dataset_id=self._cursor.dataset_id,
                version=self._cursor.version,
                position=position,
                total=self._cursor.total,
                state=self._cursor.state,
                record=record,
                completed=completed,
            )

    def seek(self, position: int) -> ReplayCursor:
        """Seek replay to a cursor position."""
        with self._lock:
            if position < 0 or position > self._cursor.total:
                msg = f"Invalid replay position: {position}"
                raise ReplayError(msg)
            current_timestamp = None
            if self._records and position < len(self._records):
                current_timestamp = self._records[position].timestamp
            self._cursor = self._cursor.model_copy(
                update={"position": position, "current_timestamp": current_timestamp}
            )
            return self._cursor

    def seek_timestamp(self, timestamp: UTCDateTime) -> ReplayCursor:
        """Seek replay to the first record at or after a timestamp."""
        with self._lock:
            position = 0
            for index, record in enumerate(self._records):
                if record.timestamp >= timestamp:
                    position = index
                    break
            else:
                position = self._cursor.total
            return self.seek(position)

    def replay_window(self, *, size: int | None = None) -> tuple[RepositoryRecord, ...]:
        """Return the next window of records without advancing the global cursor."""
        with self._lock:
            window_size = size or (self._context.window_size if self._context else 1)
            start = self._cursor.position
            end = min(start + window_size, self._cursor.total)
            return self._records[start:end]

    def pause(self) -> ReplayState:
        with self._lock:
            self._state = ReplayState.PAUSED
            self._cursor = self._cursor.model_copy(update={"state": ReplayState.PAUSED})
            return self._state

    def resume(self) -> ReplayState:
        with self._lock:
            if self._state == ReplayState.COMPLETED:
                msg = "Cannot resume a completed replay"
                raise ReplayError(msg)
            self._state = ReplayState.RUNNING
            self._cursor = self._cursor.model_copy(update={"state": ReplayState.RUNNING})
            return self._state

    def stop(self) -> ReplayState:
        with self._lock:
            self._state = ReplayState.STOPPED
            self._cursor = self._cursor.model_copy(update={"state": ReplayState.STOPPED})
            return self._state

    def reset(self) -> ReplayCursor:
        """Reset replay to the beginning."""
        with self._lock:
            if self._context is None:
                msg = "Replay context is not initialized"
                raise ReplayError(msg)
            return self.begin(self._context)
