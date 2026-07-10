"""Dataset lifecycle state definitions."""

from __future__ import annotations

from enum import StrEnum


class DatasetState(StrEnum):
    """Dataset lifecycle states."""

    DRAFT = "draft"
    REGISTERED = "registered"
    VALIDATING = "validating"
    VALIDATED = "validated"
    LOADING = "loading"
    LOADED = "loaded"
    TRANSFORMING = "transforming"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


TERMINAL_DATASET_STATES: frozenset[DatasetState] = frozenset(
    {
        DatasetState.READY,
        DatasetState.FAILED,
        DatasetState.ARCHIVED,
    }
)
