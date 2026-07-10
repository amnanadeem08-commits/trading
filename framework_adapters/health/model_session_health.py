"""Health reporting for managed model sessions."""

from __future__ import annotations

from pydantic import Field

from framework_adapters.health.health_result import HealthStatus
from framework_adapters.runtime.model_runtime_state import ModelRuntimeState
from framework_adapters.runtime.model_session_record import ModelSessionRecord
from framework_adapters.runtime.model_session_registry import (
    ModelSessionRegistry,
    build_model_session_key,
)
from models.common import PlatformModel


class ModelSessionHealthResult(PlatformModel):
    """Health metadata for a managed model session."""

    session_key: str
    model_id: str
    adapter_id: str
    status: HealthStatus
    loaded: bool = False
    ready: bool = False
    failed: bool = False
    warm: bool = False
    cached: bool = False
    idle: bool = False
    reload_required: bool = False
    message: str = ""
    details: dict[str, object] = Field(default_factory=dict)


class ModelSessionHealthChecker:
    """Reports runtime health for cached model sessions."""

    def __init__(
        self,
        *,
        session_registry: ModelSessionRegistry,
        warm: bool = False,
    ) -> None:
        self._registry = session_registry
        self._warm = warm

    def check_session(self, session_key: str) -> ModelSessionHealthResult:
        record = self._registry.lookup(session_key)
        if record is None:
            return ModelSessionHealthResult(
                session_key=session_key,
                model_id="",
                adapter_id="",
                status=HealthStatus.UNHEALTHY,
                message="model session not found",
            )
        return self._build_result(session_key, record)

    def check_model(self, model_id: str) -> tuple[ModelSessionHealthResult, ...]:
        return tuple(
            self._build_result(
                self._session_key_for(record),
                record,
            )
            for record in self._registry.list_by_model_id(model_id)
        )

    def check_all(self) -> tuple[ModelSessionHealthResult, ...]:
        return tuple(
            self._build_result(self._session_key_for(record), record)
            for record in self._registry.list_records()
        )

    def _build_result(self, session_key: str, record: object) -> ModelSessionHealthResult:
        if not isinstance(record, ModelSessionRecord):
            msg = "invalid model session record"
            raise TypeError(msg)

        loaded = record.state in {
            ModelRuntimeState.READY,
            ModelRuntimeState.RELOADING,
            ModelRuntimeState.LOADING,
        }
        ready = record.state == ModelRuntimeState.READY
        failed = record.state == ModelRuntimeState.FAILED
        idle = ready and record.reference_count > 0 and record.execution_count == 0

        if failed:
            status = HealthStatus.UNHEALTHY
            message = "model session failed"
        elif ready:
            status = HealthStatus.HEALTHY
            message = "model session ready"
        elif record.state == ModelRuntimeState.LOADING:
            status = HealthStatus.DEGRADED
            message = "model session loading"
        else:
            status = HealthStatus.DEGRADED
            message = f"model session state: {record.state.value}"

        return ModelSessionHealthResult(
            session_key=session_key,
            model_id=record.model_id,
            adapter_id=record.adapter_id,
            status=status,
            loaded=loaded,
            ready=ready,
            failed=failed,
            warm=self._warm or record.warm,
            cached=record.cached,
            idle=idle,
            reload_required=record.reload_required,
            message=message,
            details={
                "state": record.state.value,
                "reference_count": record.reference_count,
                "execution_count": record.execution_count,
            },
        )

    @staticmethod
    def _session_key_for(record: object) -> str:
        if not isinstance(record, ModelSessionRecord):
            msg = "invalid model session record"
            raise TypeError(msg)
        return build_model_session_key(
            model_id=record.model_id,
            artifact_id=record.artifact_id,
            adapter_id=record.adapter_id,
            model_version=record.model_version,
        )
