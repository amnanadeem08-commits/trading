"""Runtime executor registry."""

from __future__ import annotations

from threading import RLock

from ml_runtime.exceptions import ExecutorNotFoundError
from ml_runtime.execution.model_executor import ModelExecutor
from ml_runtime.registry.executor_registry import ExecutorMetadata, ExecutorRegistry


class RuntimeRegistry:
    """Registry for runtime executors and metadata."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._executors: dict[str, ModelExecutor] = {}
        self._metadata = ExecutorRegistry()

    def register_executor(
        self,
        executor: ModelExecutor,
        *,
        name: str,
        version: str,
        capabilities: tuple[str, ...] = (),
    ) -> ExecutorMetadata:
        executor_id = executor.executor_id()
        with self._lock:
            self._executors[executor_id] = executor
        return self._metadata.register(
            executor_id=executor_id,
            name=name,
            version=version,
            capabilities=capabilities,
        )

    def unregister_executor(self, executor_id: str) -> None:
        with self._lock:
            self._executors.pop(executor_id, None)
        self._metadata.unregister(executor_id)

    def lookup(self, executor_id: str) -> ModelExecutor:
        with self._lock:
            executor = self._executors.get(executor_id)
        if executor is None:
            raise ExecutorNotFoundError(executor_id)
        return executor

    def list(self) -> tuple[ExecutorMetadata, ...]:
        return self._metadata.list_executors()

    def clear(self) -> None:
        with self._lock:
            self._executors.clear()
        self._metadata.clear()

    def metadata(self, executor_id: str) -> ExecutorMetadata | None:
        return self._metadata.lookup(executor_id)
