"""Unit tests for ML prediction attachment."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from inference_pipeline.responses.inference_metadata import InferenceMetadata
from inference_pipeline.responses.inference_response import InferenceResponse
from inference_pipeline.responses.inference_result import InferenceStatus
from inference_pipeline.runtime.inference_response import InferenceExecutionResponse
from models.common import VersionInfo
from models.decision import DecisionSource, DecisionState
from models.prediction import SignalDirection
from signal_engine import (
    SignalAssembler,
    SignalMLAttachmentError,
    StubMLPredictionProvider,
    attach_ml_prediction,
    attach_ml_prediction_from_provider,
    ensure_ml_prediction_present,
    ml_prediction_from_inference_response,
    ml_prediction_from_normalized_output,
)
from tests.signal_helpers import make_assembly_request, make_ml_prediction


def _normalized() -> dict[str, object]:
    return {
        "direction": "BUY",
        "direction_probabilities": {"BUY": 0.6, "SELL": 0.2, "HOLD": 0.2},
        "ml_confidence": 0.66,
        "features_used": ["rsi_14", "macd"],
    }


@pytest.mark.unit
def test_ml_prediction_from_normalized_output() -> None:
    prediction = ml_prediction_from_normalized_output(
        _normalized(),
        model_name="model-a",
        model_version="1.2.3",
    )
    assert prediction.direction == SignalDirection.BUY
    assert prediction.ml_confidence == 0.66
    assert prediction.model_version.version_id == "1.2.3"


@pytest.mark.unit
def test_ml_prediction_from_inference_response() -> None:
    metadata = InferenceMetadata(
        request_id="req-1",
        model_id="model-a",
        version_id="1.0.0",
        artifact_id="art-1",
        config_hash="hash",
        checksum="sum",
        stage="execute",
        correlation_id="c1",
        trace_id="t1",
        started_at=datetime.now(UTC),
    )
    orchestration = InferenceResponse(
        request_id="req-1",
        model_id="model-a",
        status=InferenceStatus.COMPLETED,
        metadata=metadata,
    )
    response = InferenceExecutionResponse(
        request_id="req-1",
        model_id="model-a",
        status=InferenceStatus.COMPLETED,
        orchestration_response=orchestration,
        normalized_output=_normalized(),
        execution_attributes={"model_version": "ort-9"},
    )
    prediction = ml_prediction_from_inference_response(response)
    assert prediction.model_name == "model-a"
    assert prediction.model_version.version_id == "ort-9"


@pytest.mark.unit
def test_mapper_rejects_failed_or_incomplete_outputs() -> None:
    with pytest.raises(SignalMLAttachmentError, match="missing direction"):
        ml_prediction_from_normalized_output(
            {"ml_confidence": 0.5},
            model_name="m",
            model_version="1",
        )
    metadata = InferenceMetadata(
        request_id="req-1",
        model_id="model-a",
        version_id="1.0.0",
        artifact_id="art-1",
        config_hash="hash",
        checksum="sum",
        stage="execute",
        correlation_id="c1",
        trace_id="t1",
        started_at=datetime.now(UTC),
    )
    orchestration = InferenceResponse(
        request_id="req-1",
        model_id="model-a",
        status=InferenceStatus.FAILED,
        metadata=metadata,
    )
    response = InferenceExecutionResponse(
        request_id="req-1",
        model_id="model-a",
        status=InferenceStatus.FAILED,
        orchestration_response=orchestration,
        normalized_output=_normalized(),
    )
    with pytest.raises(SignalMLAttachmentError, match="completed"):
        ml_prediction_from_inference_response(response)


@pytest.mark.unit
def test_attach_ml_prediction_wires_assembler() -> None:
    prediction = make_ml_prediction()
    request = attach_ml_prediction(
        make_assembly_request(),
        prediction,
        decision_source=DecisionSource.ML_ONLY,
    )
    assert request.ml_prediction is not None
    assert request.decision == DecisionState.BUY
    assert request.decision_source == DecisionSource.ML_ONLY
    signal = SignalAssembler().assemble(request)
    assert signal.ml_prediction is not None
    assert signal.ml_prediction.model_name == "baseline"


@pytest.mark.unit
def test_attach_from_provider_and_failure_modes() -> None:
    provider = StubMLPredictionProvider()
    request = attach_ml_prediction_from_provider(
        make_assembly_request(),
        provider,
        decision_source=DecisionSource.ML_ONLY,
    )
    assert request.ml_prediction is not None

    failing = StubMLPredictionProvider(fail=True)
    with pytest.raises(SignalMLAttachmentError, match="forced failure"):
        attach_ml_prediction_from_provider(make_assembly_request(), failing)

    bare = make_assembly_request(decision_source=DecisionSource.ML_ONLY, ml_prediction=None)
    with pytest.raises(SignalMLAttachmentError, match="required"):
        ensure_ml_prediction_present(bare)

    with pytest.raises(SignalMLAttachmentError, match="decision_source"):
        attach_ml_prediction(
            make_assembly_request(),
            make_ml_prediction(),
            decision_source=DecisionSource.STATISTICAL_ONLY,
        )


@pytest.mark.unit
def test_stub_provider_requires_features() -> None:
    provider = StubMLPredictionProvider()
    with pytest.raises(SignalMLAttachmentError, match="non-empty features"):
        provider.get_prediction(symbol_id="BTC/USDT", features={})


@pytest.mark.unit
def test_mapper_edge_failures_and_hold_mapping() -> None:
    with pytest.raises(SignalMLAttachmentError, match="model_name"):
        ml_prediction_from_normalized_output(
            _normalized(),
            model_name="  ",
            model_version="1",
        )
    with pytest.raises(SignalMLAttachmentError, match="Unsupported direction"):
        ml_prediction_from_normalized_output(
            {**_normalized(), "direction": "NOPE"},
            model_name="m",
            model_version="1",
        )
    with pytest.raises(SignalMLAttachmentError, match="Probability out of range"):
        ml_prediction_from_normalized_output(
            {
                **_normalized(),
                "direction_probabilities": {"BUY": 1.5, "SELL": 0.0, "HOLD": 0.0},
            },
            model_name="m",
            model_version="1",
        )
    hold_pred = ml_prediction_from_normalized_output(
        {
            "direction": "HOLD",
            "direction_probabilities": {"BUY": 0.2, "SELL": 0.2, "HOLD": 0.6},
            "confidence": 0.4,
            "regime": "range",
        },
        model_name="m",
        model_version=VersionInfo(version_id="v2"),
        features_used=("a",),
    )
    assert hold_pred.direction == SignalDirection.HOLD
    assert hold_pred.regime == "range"
    request = attach_ml_prediction(
        make_assembly_request(),
        hold_pred,
        decision_source=DecisionSource.ML_ONLY,
    )
    assert request.decision == DecisionState.HOLD


@pytest.mark.unit
def test_provider_unexpected_exception_is_wrapped() -> None:
    class BrokenProvider:
        def get_prediction(
            self,
            *,
            symbol_id: str,
            features: dict[str, float | str | int | bool],
        ) -> object:
            raise RuntimeError("boom")

    with pytest.raises(SignalMLAttachmentError, match="provider failed"):
        attach_ml_prediction_from_provider(make_assembly_request(), BrokenProvider())  # type: ignore[arg-type]
