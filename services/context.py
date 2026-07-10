"""Application context for dependency injection."""

from __future__ import annotations

from dataclasses import dataclass

from audit.audit_logger import AuditLogger
from config.hash import compute_configuration_hash
from config.settings import AppSettings, get_settings, reset_settings
from events.event_bus import EventBus, get_event_bus, reset_event_bus
from feature_flags.manager import (
    FeatureFlagManager,
    get_feature_flag_manager,
    reset_feature_flag_manager,
)
from health.registry import HealthRegistry
from metrics.registry import MetricRegistry
from platform_logging.factory import create_logger
from platform_logging.logger import StructuredLogger
from versioning._base import VersionRegistry as ArtifactVersionRegistry
from versioning.connector_registry import (
    get_connector_version_registry,
    reset_connector_version_registry,
)
from versioning.model_registry import get_model_registry, reset_model_registry
from versioning.prompt_registry import get_prompt_registry, reset_prompt_registry
from versioning.schema_registry import get_schema_registry, reset_schema_registry
from versioning.strategy_registry import get_strategy_registry, reset_strategy_registry


class LoggerFactory:
    """Factory for creating structured loggers from application settings."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def create(self, *, service_name: str | None = None) -> StructuredLogger:
        return create_logger(self._settings.logging, service_name=service_name)


@dataclass(frozen=True)
class VersionRegistry:
    """Aggregate access to platform artifact version registries."""

    services: ArtifactVersionRegistry
    models: ArtifactVersionRegistry
    prompts: ArtifactVersionRegistry
    strategies: ArtifactVersionRegistry
    connectors: ArtifactVersionRegistry
    schemas: ArtifactVersionRegistry


@dataclass(frozen=True)
class ApplicationContext:
    """Immutable application context exposing approved platform dependencies."""

    settings: AppSettings
    feature_flags: FeatureFlagManager
    event_bus: EventBus
    metrics: MetricRegistry
    health: HealthRegistry
    audit: AuditLogger
    version_registry: VersionRegistry
    logger_factory: LoggerFactory
    configuration_hash: str


def build_application_context(
    *,
    settings: AppSettings | None = None,
    feature_flags: FeatureFlagManager | None = None,
    event_bus: EventBus | None = None,
    metrics: MetricRegistry | None = None,
    health: HealthRegistry | None = None,
    audit: AuditLogger | None = None,
    configuration_hash: str | None = None,
) -> ApplicationContext:
    """Build an application context from explicit or default dependencies."""
    resolved_settings = settings or get_settings()
    return ApplicationContext(
        settings=resolved_settings,
        feature_flags=feature_flags or get_feature_flag_manager(),
        event_bus=event_bus or get_event_bus(),
        metrics=metrics or MetricRegistry(),
        health=health or HealthRegistry(),
        audit=audit or AuditLogger(),
        version_registry=VersionRegistry(
            services=ArtifactVersionRegistry("services"),
            models=get_model_registry(),
            prompts=get_prompt_registry(),
            strategies=get_strategy_registry(),
            connectors=get_connector_version_registry(),
            schemas=get_schema_registry(),
        ),
        logger_factory=LoggerFactory(resolved_settings),
        configuration_hash=configuration_hash or compute_configuration_hash(),
    )


def reset_application_context() -> None:
    """Reset process-wide defaults used by application context construction."""
    reset_settings()
    reset_feature_flag_manager()
    reset_event_bus()
    reset_model_registry()
    reset_prompt_registry()
    reset_strategy_registry()
    reset_connector_version_registry()
    reset_schema_registry()
