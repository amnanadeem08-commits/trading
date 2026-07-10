"""Operation context contract."""

from __future__ import annotations

from pydantic import Field

from core.state.operation_state import OperationState
from models.common import PlatformModel


class OperationContext(PlatformModel):
    """Context describing the active core operation."""

    operation_id: str = Field(min_length=1)
    operation_type: str = Field(min_length=1)
    state: OperationState = OperationState.INITIALIZED
    parent_operation_id: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
