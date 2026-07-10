"""Stub executor factory delegating to Task 12 StubModelExecutor."""

from __future__ import annotations

from ml_engine_plugins.engines.stub_executor import STUB_ENGINE_ID, StubModelExecutor
from ml_runtime.execution.model_executor import ModelExecutor


class StubExecutorFactory:
    """Creates StubModelExecutor instances without duplicating executor logic."""

    def create(self, *, executor_id: str = STUB_ENGINE_ID) -> ModelExecutor:
        """Return the existing metadata-only stub executor."""
        return StubModelExecutor(executor_id=executor_id)
