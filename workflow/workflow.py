"""Workflow definition contract."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel
from workflow.job import Job


class Workflow(PlatformModel):
    """A workflow composed of one or more managed jobs."""

    workflow_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    jobs: tuple[Job, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
