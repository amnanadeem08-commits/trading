"""Inference options contract."""

from __future__ import annotations

from models.common import PlatformModel


class InferenceOptions(PlatformModel):
    """Options controlling inference orchestration."""

    timeout_seconds: int = 60
    batch_size: int = 1
    priority: int = 0
    trace_enabled: bool = True
    reproducibility_key: str = ""
