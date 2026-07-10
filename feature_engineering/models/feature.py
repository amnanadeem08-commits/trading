"""Single feature value contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class Feature(PlatformModel):
    """Generic named feature value."""

    name: str = Field(min_length=1)
    value: float | str | int | bool = 0.0
    dtype: str = Field(min_length=1, default="float")
    source_field: str = ""
