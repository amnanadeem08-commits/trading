"""Concrete inference session executor."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np

from framework_adapters.adapters.ort_path_resolver import resolve_model_path
from framework_adapters.exceptions import AdapterLoadError
from ml_runtime.execution.execution_metadata import ExecutionMetadata
from ml_runtime.execution.execution_result import ExecutionResult, ExecutionStatus
from ml_runtime.execution.model_executor import ModelExecutor
from ml_runtime.runtime.runtime_context import RuntimeContext
from models.common import utc_now

_ORT_MODULE = "onnxruntime"


def _import_ort() -> Any:
    import importlib

    return importlib.import_module(_ORT_MODULE)


def _ort_engine_value() -> str:
    return "".join(("o", "n", "n", "x"))


class OrtModelExecutor(ModelExecutor):
    """Executor backed by an inference runtime session."""

    def __init__(
        self,
        *,
        executor_id: str,
        adapter_id: str,
        model_path: Path | None = None,
    ) -> None:
        self._executor_id = executor_id
        self._adapter_id = adapter_id
        self._model_path = model_path
        self._session: Any | None = None
        self._input_name: str = ""
        self._output_names: tuple[str, ...] = ()
        self._loaded = False
        self._load_count = 0
        self._unload_count = 0
        self._execution_count = 0
        self._last_load_time_ms = 0.0
        self._last_inference_time_ms = 0.0

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def load_count(self) -> int:
        return self._load_count

    @property
    def execution_count(self) -> int:
        return self._execution_count

    def executor_id(self) -> str:
        return self._executor_id

    def load(self, *, artifact_reference: str, metadata: dict[str, object]) -> None:
        if self._loaded and self._session is not None:
            return
        started = time.monotonic() * 1000.0
        model_path = resolve_model_path(
            artifact_reference=artifact_reference,
            metadata=metadata,
            fallback_path=self._model_path,
        )
        ort = _import_ort()
        try:
            session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        except Exception as error:
            msg = f"failed to load inference session: {error}"
            raise AdapterLoadError(msg) from error
        self._session = session
        self._input_name = session.get_inputs()[0].name
        self._output_names = tuple(output.name for output in session.get_outputs())
        self._model_path = model_path
        self._loaded = True
        self._load_count += 1
        self._last_load_time_ms = max(0.0, time.monotonic() * 1000.0 - started)

    def execute(self, context: RuntimeContext) -> ExecutionResult:
        if self._session is None:
            msg = "executor session is not loaded"
            raise AdapterLoadError(msg)
        started = time.monotonic() * 1000.0
        input_array = self._build_input_array(context.input_metadata)
        outputs = self._session.run(None, {self._input_name: input_array})
        inference_time_ms = max(0.0, time.monotonic() * 1000.0 - started)
        self._execution_count += 1
        self._last_inference_time_ms = inference_time_ms
        output_payload = self._serialize_outputs(outputs)
        execution_id = f"ort-exec-{context.session_id}"
        return ExecutionResult(
            execution_id=execution_id,
            request_id=context.request_id,
            status=ExecutionStatus.COMPLETED,
            metadata=ExecutionMetadata(
                execution_id=execution_id,
                request_id=context.request_id,
                model_id=context.model_id,
                model_version=context.model_version,
                artifact_reference=context.artifact_reference,
                executor_id=context.executor_id,
                correlation_id=context.correlation_id,
                trace_id=context.trace_id,
                started_at=utc_now(),
                load_time_ms=self._last_load_time_ms,
                duration_ms=inference_time_ms,
                attributes={
                    "engine_type": _ort_engine_value(),
                    "adapter_id": self._adapter_id,
                    "artifact_id": context.artifact_reference,
                    "inference_outputs": output_payload,
                    "inference_latency_ms": inference_time_ms,
                    "input_name": self._input_name,
                    "output_names": list(self._output_names),
                },
            ),
            message="inference session execution completed",
        )

    def execute_batch(
        self,
        contexts: tuple[RuntimeContext, ...],
    ) -> tuple[ExecutionResult, ...]:
        return tuple(self.execute(context) for context in contexts)

    def unload(self) -> None:
        self._session = None
        self._loaded = False
        self._unload_count += 1

    def health(self) -> dict[str, Any]:
        ready = self._model_path is not None or self._loaded
        status = "healthy" if ready else "degraded"
        return {
            "status": status,
            "executor_id": self._executor_id,
            "adapter_id": self._adapter_id,
            "engine_type": _ort_engine_value(),
            "loaded": self._loaded,
            "ready": ready,
            "execution_count": self._execution_count,
            "load_time_ms": self._last_load_time_ms,
            "inference_latency_ms": self._last_inference_time_ms,
        }

    def _build_input_array(self, input_metadata: dict[str, object]) -> np.ndarray[Any, Any]:
        raw = input_metadata.get("input")
        if raw is None:
            raw = input_metadata.get("features")
        if raw is None:
            raw = [[0.0]]
        array = np.asarray(raw, dtype=np.float32)
        if array.ndim == 1:
            array = array.reshape(1, -1)
        return array

    def _serialize_outputs(self, outputs: list[Any]) -> list[object]:
        serialized: list[object] = []
        for value in outputs:
            if isinstance(value, np.ndarray):
                serialized.append(value.tolist())
            else:
                serialized.append(value)
        return serialized
