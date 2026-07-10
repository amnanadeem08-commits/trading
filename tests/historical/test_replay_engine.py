"""Unit tests for replay engine."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from historical import ReplayContext, ReplayEngine, ReplayError, ReplayState, Repository
from tests.historical_helpers import seed_repository


def test_replay_from_beginning() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = ReplayEngine(repository)
    cursor = engine.begin(
        ReplayContext(dataset_id="dataset-1", version="1.0.0", deterministic=True)
    )
    assert cursor.total == 3
    assert cursor.state == ReplayState.RUNNING
    first = engine.next()
    assert first is not None
    assert first.record is not None
    assert first.position == 1


def test_replay_by_timestamp() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = ReplayEngine(repository)
    timestamp = datetime(2026, 1, 1, 12, 2, 0, tzinfo=UTC)
    engine.begin(
        ReplayContext(
            dataset_id="dataset-1",
            version="1.0.0",
            start_timestamp=timestamp,
        )
    )
    result = engine.next()
    assert result is not None
    assert result.record is not None
    assert result.record.sequence == 2


def test_replay_seek_and_window() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = ReplayEngine(repository)
    engine.begin(ReplayContext(dataset_id="dataset-1", version="1.0.0"))
    engine.seek(1)
    window = engine.replay_window(size=2)
    assert len(window) == 2
    assert window[0].sequence == 1


def test_replay_pause_resume_stop() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = ReplayEngine(repository)
    engine.begin(ReplayContext(dataset_id="dataset-1", version="1.0.0"))
    assert engine.pause() == ReplayState.PAUSED
    assert engine.resume() == ReplayState.RUNNING
    assert engine.stop() == ReplayState.STOPPED
    assert engine.next() is None


def test_replay_reset() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = ReplayEngine(repository)
    engine.begin(ReplayContext(dataset_id="dataset-1", version="1.0.0"))
    engine.next()
    cursor = engine.reset()
    assert cursor.position == 0


def test_replay_seek_invalid_raises() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = ReplayEngine(repository)
    engine.begin(ReplayContext(dataset_id="dataset-1", version="1.0.0"))
    with pytest.raises(ReplayError):
        engine.seek(99)
