"""Stub model executor for metadata-only runtime validation."""

from __future__ import annotations

from typing import Any

from ml_runtime.execution.execution_metadata import ExecutionMetadata
from ml_runtime.execution.execution_result import ExecutionResult, ExecutionStatus
from ml_runtime.execution.model_executor import ModelExecutor
from ml_runtime.runtime.runtime_context import RuntimeContext
from models.common import utc_now

STUB_ENGINE_ID = "stub-engine"


class StubModelExecutor(ModelExecutor):
    """Metadata-only executor. No ML framework binding."""

    def __init__(self, *, executor_id: str = STUB_ENGINE_ID) -> None:
        self._executor_id = executor_id
        self._loaded = False
        self._load_count = 0
        self._unload_count = 0

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def load_count(self) -> int:
        return self._load_count

    @property
    def unload_count(self) -> int:
        return self._unload_count

    def executor_id(self) -> str:
        return self._executor_id

    def load(self, *, artifact_reference: str, metadata: dict[str, object]) -> None:
        self._loaded = True
        self._load_count += 1
        _ = artifact_reference, metadata

    def execute(self, context: RuntimeContext) -> ExecutionResult:
        return ExecutionResult(
            execution_id=f"stub-exec-{context.session_id}",
            request_id=context.request_id,
            status=ExecutionStatus.COMPLETED,
            metadata=ExecutionMetadata(
                execution_id=f"stub-exec-{context.session_id}",
                request_id=context.request_id,
                model_id=context.model_id,
                model_version=context.model_version,
                artifact_reference=context.artifact_reference,
                executor_id=context.executor_id,
                correlation_id=context.correlation_id,
                trace_id=context.trace_id,
                started_at=utc_now(),
                attributes={"engine_type": "stub"},
            ),
            message="stub engine execution completed",
        )

    def execute_batch(
        self,
        contexts: tuple[RuntimeContext, ...],
    ) -> tuple[ExecutionResult, ...]:
        return tuple(self.execute(context) for context in contexts)

    def unload(self) -> None:
        self._loaded = False
        self._unload_count += 1

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "executor_id": self._executor_id,
            "engine_type": "stub",
            "loaded": self._loaded,
        }
