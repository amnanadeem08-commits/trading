"""Pipeline execution context."""

from __future__ import annotations

from dataclasses import dataclass

from audit.audit_logger import AuditLogger
from config.settings import AppSettings
from events.event_bus import EventBus
from health.registry import HealthRegistry
from metrics.registry import MetricRegistry
from services.context import ApplicationContext, VersionRegistry


@dataclass(frozen=True)
class PipelineContext:
    """Execution context exposing approved platform dependencies."""

    settings: AppSettings
    application: ApplicationContext

    @property
    def event_bus(self) -> EventBus:
        return self.application.event_bus

    @property
    def metrics(self) -> MetricRegistry:
        return self.application.metrics

    @property
    def health(self) -> HealthRegistry:
        return self.application.health

    @property
    def audit(self) -> AuditLogger:
        return self.application.audit

    @property
    def version_registry(self) -> VersionRegistry:
        return self.application.version_registry


def build_pipeline_context(application: ApplicationContext | None = None) -> PipelineContext:
    """Build a pipeline context from an application context."""
    from services.context import build_application_context

    resolved = application or build_application_context()
    return PipelineContext(settings=resolved.settings, application=resolved)
