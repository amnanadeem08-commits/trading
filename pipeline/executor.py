"""Pipeline stage executor."""

from __future__ import annotations

import time

from health.models import HealthState
from models.common import VersionInfo, utc_now
from pipeline.context import PipelineContext
from pipeline.exceptions import (
    PipelineCancelledError,
    PipelineTimeoutError,
    PipelineValidationError,
    StageExecutionError,
)
from pipeline.lifecycle import (
    CancellationToken,
    PipelineLifecycleEventType,
    PipelineLifecycleManager,
)
from pipeline.pipeline import Pipeline
from pipeline.request import PipelineRequest
from pipeline.response import PipelineResponse
from pipeline.result import PipelineResult, PipelineStatus, StageResult, StageStatus
from pipeline.stage import PipelineStage
from pipeline.validation import validate_pipeline_stages


class PipelineExecutor:
    """Executes pipeline stages with timing, rollback, and observability."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lifecycle = PipelineLifecycleManager(context)

    @property
    def lifecycle(self) -> PipelineLifecycleManager:
        return self._lifecycle

    def execute(
        self,
        pipeline: Pipeline,
        request: PipelineRequest,
        *,
        cancellation: CancellationToken | None = None,
    ) -> PipelineResponse:
        """Execute a pipeline for the given request."""
        token = cancellation or CancellationToken()
        validation = validate_pipeline_stages(pipeline.stages)
        if not validation.valid:
            msg = "Pipeline validation failed"
            raise PipelineValidationError(msg, errors=validation.errors)

        errors: list[str] = []
        warnings: list[str] = []
        stage_results: list[StageResult] = []
        completed_stages: list[str] = []
        timings: dict[str, float] = {}
        metrics: dict[str, object] = {}
        pipeline_started = time.perf_counter()

        self._lifecycle.emit(
            PipelineLifecycleEventType.PIPELINE_STARTED,
            pipeline_name=pipeline.name,
            pipeline_version=pipeline.version,
            request=request,
            message="pipeline started",
        )

        try:
            first_stage = self._first_stage(pipeline)
            last_stage = self._last_stage(pipeline)
            for pre_hook in pipeline.pre_hooks:
                pre_hook(self._context, request, first_stage)

            for stage_name in validation.execution_order:
                self._check_cancellation(pipeline, token)
                if completed_stages and pipeline.shutdown_requested:
                    warnings.append("pipeline shutdown requested")
                    break

                stage = pipeline.stages[stage_name]
                self._register_stage_observability(stage)
                for before_hook in pipeline.before_stage_hooks:
                    before_hook(self._context, request, stage)

                self._lifecycle.emit(
                    PipelineLifecycleEventType.STAGE_STARTED,
                    pipeline_name=pipeline.name,
                    pipeline_version=pipeline.version,
                    request=request,
                    stage_name=stage_name,
                    message="stage started",
                )

                stage_started = time.perf_counter()
                latest_stage_result: StageResult | None = None
                try:
                    stage.validate(self._context, request)
                    stage_result = self._execute_stage_with_timeout(
                        pipeline,
                        stage,
                        request,
                    )
                    latest_stage_result = stage_result
                    stage_results.append(stage_result)
                    completed_stages.append(stage_name)
                    timings[stage_name] = stage_result.duration_ms
                    self._context.metrics.counter(f"pipeline.stage.{stage_name}.success").inc(1)
                    self._lifecycle.emit(
                        PipelineLifecycleEventType.STAGE_COMPLETED,
                        pipeline_name=pipeline.name,
                        pipeline_version=pipeline.version,
                        request=request,
                        stage_name=stage_name,
                        message=stage_result.message,
                    )
                except Exception as error:
                    duration_ms = (time.perf_counter() - stage_started) * 1000.0
                    failed = StageResult(
                        stage_name=stage_name,
                        stage_version=stage.version(),
                        status=StageStatus.FAILED,
                        message=str(error),
                        duration_ms=duration_ms,
                        completed_at=utc_now(),
                    )
                    latest_stage_result = failed
                    stage_results.append(failed)
                    timings[stage_name] = duration_ms
                    errors.append(str(error))
                    self._context.metrics.counter(f"pipeline.stage.{stage_name}.failure").inc(1)
                    self._lifecycle.emit(
                        PipelineLifecycleEventType.STAGE_FAILED,
                        pipeline_name=pipeline.name,
                        pipeline_version=pipeline.version,
                        request=request,
                        stage_name=stage_name,
                        message=str(error),
                    )
                    rollback_errors = self._rollback_stages(
                        pipeline,
                        request,
                        completed_stages,
                    )
                    errors.extend(rollback_errors)
                    pipeline_result = self._build_result(
                        pipeline,
                        PipelineStatus.FAILED,
                        errors,
                        warnings,
                        metrics,
                        timings,
                        stage_results,
                        pipeline_started,
                    )
                    self._lifecycle.emit(
                        PipelineLifecycleEventType.PIPELINE_FAILED,
                        pipeline_name=pipeline.name,
                        pipeline_version=pipeline.version,
                        request=request,
                        message="pipeline failed",
                    )
                    self._run_cleanup(pipeline, request, completed_stages)
                    return PipelineResponse(request=request, result=pipeline_result)
                finally:
                    if latest_stage_result is not None:
                        for after_hook in pipeline.after_stage_hooks:
                            after_hook(self._context, request, stage, latest_stage_result)

            for post_hook in pipeline.post_hooks:
                post_hook(self._context, request, last_stage)

            status = PipelineStatus.CANCELLED if token.is_cancelled() else PipelineStatus.COMPLETED
            pipeline_result = self._build_result(
                pipeline,
                status,
                errors,
                warnings,
                metrics,
                timings,
                stage_results,
                pipeline_started,
            )
            event_type = (
                PipelineLifecycleEventType.PIPELINE_FAILED
                if status == PipelineStatus.CANCELLED
                else PipelineLifecycleEventType.PIPELINE_COMPLETED
            )
            self._lifecycle.emit(
                event_type,
                pipeline_name=pipeline.name,
                pipeline_version=pipeline.version,
                request=request,
                message=status.value,
            )
            self._run_cleanup(pipeline, request, completed_stages)
            return PipelineResponse(request=request, result=pipeline_result)
        except PipelineCancelledError as error:
            errors.append(str(error))
            pipeline_result = self._build_result(
                pipeline,
                PipelineStatus.CANCELLED,
                errors,
                warnings,
                metrics,
                timings,
                stage_results,
                pipeline_started,
            )
            self._lifecycle.emit(
                PipelineLifecycleEventType.PIPELINE_FAILED,
                pipeline_name=pipeline.name,
                pipeline_version=pipeline.version,
                request=request,
                message="pipeline cancelled",
            )
            return PipelineResponse(request=request, result=pipeline_result)

    def _execute_stage_with_timeout(
        self,
        pipeline: Pipeline,
        stage: PipelineStage,
        request: PipelineRequest,
    ) -> StageResult:
        timeout_seconds = pipeline.settings.stage_timeout_seconds
        started = time.perf_counter()
        stage_result = stage.execute(self._context, request)
        elapsed = time.perf_counter() - started
        if elapsed > timeout_seconds:
            raise PipelineTimeoutError(stage.name(), timeout_seconds)
        if stage_result.duration_ms == 0.0:
            stage_result = stage_result.model_copy(update={"duration_ms": elapsed * 1000.0})
        if stage_result.status == StageStatus.FAILED:
            raise StageExecutionError(stage.name(), stage_result.message)
        return stage_result

    def _rollback_stages(
        self,
        pipeline: Pipeline,
        request: PipelineRequest,
        completed_stages: list[str],
    ) -> list[str]:
        errors: list[str] = []
        if not pipeline.settings.rollback_enabled:
            return errors
        for stage_name in reversed(completed_stages):
            stage = pipeline.stages[stage_name]
            try:
                stage.rollback(self._context, request)
            except Exception as error:
                errors.append(f"rollback failed for {stage_name}: {error}")
        return errors

    def _run_cleanup(
        self,
        pipeline: Pipeline,
        request: PipelineRequest,
        completed_stages: list[str],
    ) -> None:
        if not pipeline.settings.cleanup_enabled:
            return
        for stage_name in completed_stages:
            stage = pipeline.stages[stage_name]
            try:
                stage.cleanup(self._context, request)
            except Exception:
                continue

    def _register_stage_observability(self, stage: PipelineStage) -> None:
        stage_name = stage.name()
        self._context.health.register(
            f"pipeline.stage.{stage_name}",
            lambda: (HealthState.HEALTHY, "pipeline stage ready"),
            dependencies=stage.dependencies(),
        )
        self._context.metrics.gauge(f"pipeline.stage.{stage_name}.ready").set(1.0)
        self._context.application.logger_factory.create(service_name=f"pipeline.{stage_name}")
        version_id = stage.version()
        if not self._context.version_registry.services.exists(version_id):
            self._context.version_registry.services.register(
                VersionInfo(version_id=version_id, description=stage_name),
            )

    def _check_cancellation(self, pipeline: Pipeline, token: CancellationToken) -> None:
        if token.is_cancelled():
            raise PipelineCancelledError(pipeline.name)

    def _first_stage(self, pipeline: Pipeline) -> PipelineStage:
        order = pipeline.stage_order()
        if not order:
            msg = "Pipeline has no stages"
            raise PipelineValidationError(msg)
        return pipeline.stages[order[0]]

    def _last_stage(self, pipeline: Pipeline) -> PipelineStage:
        order = pipeline.stage_order()
        if not order:
            msg = "Pipeline has no stages"
            raise PipelineValidationError(msg)
        return pipeline.stages[order[-1]]

    def _build_result(
        self,
        pipeline: Pipeline,
        status: PipelineStatus,
        errors: list[str],
        warnings: list[str],
        metrics: dict[str, object],
        timings: dict[str, float],
        stage_results: list[StageResult],
        pipeline_started: float,
    ) -> PipelineResult:
        total_ms = (time.perf_counter() - pipeline_started) * 1000.0
        metrics["pipeline.total_duration_ms"] = total_ms
        metrics["pipeline.stage_count"] = len(stage_results)
        return PipelineResult(
            pipeline_name=pipeline.name,
            status=status,
            errors=tuple(errors),
            warnings=tuple(warnings),
            metrics=metrics,
            timings=timings,
            stage_results=tuple(stage_results),
            completed_at=utc_now(),
        )
