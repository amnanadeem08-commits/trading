"""Adapter capability contracts."""

from __future__ import annotations

from enum import StrEnum


class AdapterCapability(StrEnum):
    """Supported framework adapter abilities. Metadata only."""

    LOAD_ARTIFACT = "load_artifact"
    BATCH_EXECUTION = "batch_execution"
    ONLINE_EXECUTION = "online_execution"
    GPU_SUPPORTED = "gpu_supported"
    CPU_SUPPORTED = "cpu_supported"
    QUANTIZATION = "quantization"
    DISTRIBUTED = "distributed"
