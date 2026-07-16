"""Deterministic prediction outcome validation foundation (V1.3).

Disclaimer: validation metrics measure historical prediction accuracy for research
and learning only. They are **not** financial advice and do not guarantee future
performance.
"""

from __future__ import annotations

from prediction_validation.contracts import (
    ConfidenceCalibrationBucket,
    PredictionRecord,
    PredictionValidationConfig,
    PredictionValidationSummary,
    ValidationOutcomeRecord,
    ValidationStatus,
)
from prediction_validation.engine import (
    PredictionValidationService,
    PredictionValidationStore,
    compute_prediction_validation_summary,
    evaluate_prediction_outcome,
)
from prediction_validation.exceptions import (
    LookAheadValidationError,
    PredictionImmutableError,
    PredictionNotFoundError,
    PredictionValidationError,
)

__all__ = [
    "ConfidenceCalibrationBucket",
    "LookAheadValidationError",
    "PredictionImmutableError",
    "PredictionNotFoundError",
    "PredictionRecord",
    "PredictionValidationConfig",
    "PredictionValidationError",
    "PredictionValidationService",
    "PredictionValidationStore",
    "PredictionValidationSummary",
    "ValidationOutcomeRecord",
    "ValidationStatus",
    "compute_prediction_validation_summary",
    "evaluate_prediction_outcome",
]
