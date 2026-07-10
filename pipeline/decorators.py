"""Stage registration decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from pipeline.stage import PipelineStage

StageType = TypeVar("StageType", bound=type[PipelineStage])

_STAGE_METADATA_KEY = "_platform_stage_metadata"


def stage(
    *,
    name: str | None = None,
    auto_register: bool = True,
) -> Callable[[StageType], StageType]:
    """Mark a stage class for discovery and optional auto-registration."""

    def decorator(cls: StageType) -> StageType:
        setattr(
            cls,
            _STAGE_METADATA_KEY,
            {
                "name": name,
                "auto_register": auto_register,
            },
        )
        return cls

    return decorator


def stage_metadata(stage_type: type[PipelineStage]) -> dict[str, str | bool | None]:
    """Return discovery metadata attached to a stage class."""
    metadata = getattr(stage_type, _STAGE_METADATA_KEY, None)
    if metadata is None:
        return {"name": None, "auto_register": False}
    return dict(metadata)
