"""Replay cursor contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime


class ReplayState(StrEnum):
    """Replay session states."""

    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


class ReplayCursor(PlatformModel):
    """Position within a replay session."""

    dataset_id: str = Field(default="pending", min_length=1)
    version: str = Field(default="pending", min_length=1)
    position: int = Field(ge=0, default=0)
    total: int = Field(ge=0, default=0)
    state: ReplayState = ReplayState.READY
    current_timestamp: UTCDateTime | None = None
