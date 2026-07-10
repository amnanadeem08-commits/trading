"""Replay result contracts."""

from __future__ import annotations

from pydantic import Field

from historical.replay.replay_cursor import ReplayState
from historical.storage.repository_record import RepositoryRecord
from models.common import PlatformModel


class ReplayResult(PlatformModel):
    """Outcome of a replay step."""

    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    position: int = Field(ge=0, default=0)
    total: int = Field(ge=0, default=0)
    state: ReplayState = ReplayState.RUNNING
    record: RepositoryRecord | None = None
    completed: bool = False
