"""Prompt contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class Prompt(PlatformModel):
    """Registered prompt definition."""

    prompt_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    content: str = Field(min_length=1)
    description: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
