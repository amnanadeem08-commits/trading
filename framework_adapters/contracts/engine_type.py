"""Engine type enumeration."""

from __future__ import annotations

from enum import StrEnum


class EngineType(StrEnum):
    """Supported ML engine types. Enum only; no framework bindings."""

    STUB = "stub"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    ONNX = "onnx"
    SKLEARN = "sklearn"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    CUSTOM = "custom"
