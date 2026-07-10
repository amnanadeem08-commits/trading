"""Runtime state identifiers for managed model sessions."""

from __future__ import annotations

from enum import StrEnum


class ModelRuntimeState(StrEnum):
    """Lifecycle states for adapter-managed model sessions."""

    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"
    RELOADING = "reloading"
