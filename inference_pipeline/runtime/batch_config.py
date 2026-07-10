"""Batch execution configuration abstraction."""

from __future__ import annotations

from models.common import PlatformModel


class BatchConfig(PlatformModel):
    """Batch settings for future multi-sample execution."""

    batch_size: int = 1
    batch_dimension: int = 0
    future_batch_execution: bool = False
