"""Workflow registration decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from workflow.workflow import Workflow

WorkflowType = TypeVar("WorkflowType", bound=Workflow)


_WORKFLOW_METADATA_KEY = "_platform_workflow_metadata"


def workflow(
    *,
    workflow_id: str | None = None,
    auto_register: bool = True,
) -> Callable[[WorkflowType], WorkflowType]:
    """Attach discovery metadata to a workflow definition."""

    def decorator(defn: WorkflowType) -> WorkflowType:
        setattr(
            defn,
            _WORKFLOW_METADATA_KEY,
            {
                "workflow_id": workflow_id,
                "auto_register": auto_register,
            },
        )
        return defn

    return decorator


def workflow_metadata(defn: type[Workflow] | Workflow) -> dict[str, str | bool | None]:
    """Return discovery metadata attached to a workflow definition."""
    metadata = getattr(defn, _WORKFLOW_METADATA_KEY, None)
    if metadata is None:
        return {"workflow_id": None, "auto_register": False}
    return dict(metadata)
