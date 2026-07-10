"""Application settings. Pydantic Settings with YAML and environment overrides."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.loader import load_yaml_config, merge_configs
from models.common import ConfigurationError, PlatformModel


class IndicatorSettings(PlatformModel):
    """Technical indicator parameters. Loaded from config/indicators.yaml."""

    rsi_period: int = Field(ge=1, default=14)
    macd_fast: int = Field(ge=1, default=12)
    macd_slow: int = Field(ge=1, default=26)
    macd_signal: int = Field(ge=1, default=9)


class RiskSettings(PlatformModel):
    """Risk layer configuration."""

    registry_enabled: bool = True
    max_engines: int = Field(ge=1, default=100)
    policy_enabled: bool = True
    validation_enabled: bool = True
    scoring_enabled: bool = True
    lifecycle_enabled: bool = True
    versioning_enabled: bool = True


class FeatureFlagSettings(PlatformModel):
    """Runtime feature flags per Rule R17."""

    signal_only: bool = True
    ai_enabled: bool = True
    multi_agent_enabled: bool = False
    rag_enabled: bool = False
    memory_enabled: bool = False
    news_enabled: bool = False
    macro_enabled: bool = False
    live_trading_enabled: bool = False
    pmex_enabled: bool = False
    experimental_mode: bool = False


class MarketEntry(PlatformModel):
    """Single market registration entry."""

    market_id: str = Field(min_length=1)
    connector_class: str = Field(min_length=1)
    enabled: bool = False
    display_name: str = Field(min_length=1)


class LoggingSettings(PlatformModel):
    """Structured logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: Literal["json", "text"] = "json"
    include_correlation_id: bool = True
    include_trace_id: bool = True
    include_request_id: bool = True
    file_path: str | None = None
    console_enabled: bool = True


class MonitoringSettings(PlatformModel):
    """Monitoring and observability configuration."""

    enabled: bool = True
    heartbeat_interval_seconds: int = Field(ge=1, default=30)
    startup_check_timeout_seconds: int = Field(ge=1, default=10)
    shutdown_check_timeout_seconds: int = Field(ge=1, default=10)
    collect_system_info: bool = True


class ServiceSettings(PlatformModel):
    """Platform service layer configuration."""

    auto_discovery: bool = True
    graceful_shutdown: bool = True
    startup_validation: bool = True
    shutdown_validation: bool = True
    startup_timeout_seconds: int = Field(ge=1, default=30)
    shutdown_timeout_seconds: int = Field(ge=1, default=30)


class PipelineSettings(PlatformModel):
    """Pipeline engine configuration."""

    stage_timeout_seconds: int = Field(ge=1, default=60)
    pipeline_timeout_seconds: int = Field(ge=1, default=300)
    rollback_enabled: bool = True
    cleanup_enabled: bool = True
    graceful_shutdown: bool = True
    cancellation_enabled: bool = True
    max_stages: int = Field(ge=1, default=50)


class WorkflowSettings(PlatformModel):
    """Workflow runtime configuration."""

    job_timeout_seconds: int = Field(ge=1, default=300)
    workflow_timeout_seconds: int = Field(ge=1, default=3600)
    checkpoint_enabled: bool = True
    recovery_enabled: bool = True
    queue_enabled: bool = True
    max_jobs_per_workflow: int = Field(ge=1, default=50)
    graceful_shutdown: bool = True


class DataSettings(PlatformModel):
    """Data layer configuration."""

    max_datasets: int = Field(ge=1, default=100)
    cache_enabled: bool = True
    cache_max_entries: int = Field(ge=1, default=100)
    validation_enabled: bool = True
    lineage_enabled: bool = True
    provenance_enabled: bool = True
    persistence_enabled: bool = True
    max_schema_fields: int = Field(ge=1, default=200)


class CoreSettings(PlatformModel):
    """Core runtime configuration."""

    context_enabled: bool = True
    audit_enabled: bool = True
    security_enabled: bool = True
    max_entities: int = Field(ge=1, default=100)
    trace_enabled: bool = True
    lifecycle_enabled: bool = True


class MlSettings(PlatformModel):
    """ML layer configuration."""

    registry_enabled: bool = True
    max_models: int = Field(ge=1, default=100)
    training_enabled: bool = True
    inference_enabled: bool = True
    evaluation_enabled: bool = True
    feature_pipeline_enabled: bool = True
    lifecycle_enabled: bool = True
    versioning_enabled: bool = True


class AiSettings(PlatformModel):
    """AI layer configuration."""

    registry_enabled: bool = True
    max_agents: int = Field(ge=1, default=100)
    orchestration_enabled: bool = True
    prompt_enabled: bool = True
    llm_enabled: bool = True
    reasoning_enabled: bool = True
    memory_enabled: bool = True
    evaluation_enabled: bool = True
    lifecycle_enabled: bool = True
    versioning_enabled: bool = True


class DecisionSettings(PlatformModel):
    """Decision layer configuration."""

    registry_enabled: bool = True
    max_engines: int = Field(ge=1, default=100)
    policy_enabled: bool = True
    evaluation_enabled: bool = True
    lifecycle_enabled: bool = True
    versioning_enabled: bool = True


class ExecutionSettings(PlatformModel):
    """Execution layer configuration."""

    registry_enabled: bool = True
    max_engines: int = Field(ge=1, default=100)
    validation_enabled: bool = True
    dispatch_enabled: bool = True
    lifecycle_enabled: bool = True
    versioning_enabled: bool = True
    queue_max_size: int = Field(ge=1, default=1000)


class ConnectorSettings(PlatformModel):
    """Connector framework configuration."""

    registry_enabled: bool = True
    max_adapters: int = Field(ge=1, default=100)
    validation_enabled: bool = True
    dispatch_bridge_enabled: bool = True
    lifecycle_enabled: bool = True
    versioning_enabled: bool = True


class PaperAdapterSettings(PlatformModel):
    """Paper execution adapter configuration."""

    enabled: bool = True
    deterministic: bool = True
    random_seed: int = 42
    failure_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    latency_ms_min: int = Field(ge=0, default=1)
    latency_ms_max: int = Field(ge=0, default=50)
    simulate_delay: bool = False


class HistoricalSettings(PlatformModel):
    """Historical data repository configuration."""

    storage_backend: str = "in_memory"
    cache_enabled: bool = True
    versioning_enabled: bool = True
    replay_enabled: bool = True
    validation_enabled: bool = True


class PluginSettings(PlatformModel):
    """Plugin framework configuration."""

    auto_discovery: bool = True
    startup_validation: bool = True
    max_plugins: int = Field(ge=1, default=100)
    graceful_shutdown: bool = True
    sandbox_enabled: bool = False
    platform_version: str = Field(min_length=1, default="0.1.0")
    platform_api_version: str = Field(min_length=1, default="1.0.0")


class SecuritySettings(PlatformModel):
    """Security scaffold configuration."""

    rbac_enabled: bool = False
    token_ttl_seconds: int = Field(ge=1, default=3600)
    encryption_algorithm: str = Field(min_length=1, default="aes-256-gcm")
    hash_algorithm: str = Field(min_length=1, default="sha256")
    audit_security_events: bool = True


class NotificationSettings(PlatformModel):
    """Notification scaffold configuration."""

    enabled: bool = False
    default_channel: Literal["email", "slack", "webhook"] = "webhook"
    retry_attempts: int = Field(ge=0, default=3)
    retry_delay_seconds: int = Field(ge=0, default=5)
    batch_size: int = Field(ge=1, default=10)


class DatabaseSettings(PlatformModel):
    """Database connection settings."""

    url: str = Field(
        default="postgresql://trading:trading@localhost:5432/trading",
        min_length=1,
    )
    pool_size: int = Field(ge=1, default=5)
    echo: bool = False


class RedisSettings(PlatformModel):
    """Redis settings for queue and cache."""

    url: str = Field(default="redis://localhost:6379/0", min_length=1)


class AppSettings(BaseSettings):
    """Root application settings. Environment variables override YAML."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "trading-platform"
    environment: Literal["development", "staging", "production"] = "development"
    schema_version: str = "1.0.0"
    timezone_internal: Literal["UTC"] = "UTC"

    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    services: ServiceSettings = Field(default_factory=ServiceSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    workflow: WorkflowSettings = Field(default_factory=WorkflowSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    core: CoreSettings = Field(default_factory=CoreSettings)
    ml: MlSettings = Field(default_factory=MlSettings)
    ai: AiSettings = Field(default_factory=AiSettings)
    decision: DecisionSettings = Field(default_factory=DecisionSettings)
    plugins: PluginSettings = Field(default_factory=PluginSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    indicators: IndicatorSettings = Field(default_factory=IndicatorSettings)
    risk: RiskSettings = Field(default_factory=RiskSettings)
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)
    connectors: ConnectorSettings = Field(default_factory=ConnectorSettings)
    paper_adapter: PaperAdapterSettings = Field(default_factory=PaperAdapterSettings)
    historical: HistoricalSettings = Field(default_factory=HistoricalSettings)
    feature_flags: FeatureFlagSettings = Field(default_factory=FeatureFlagSettings)
    markets: tuple[MarketEntry, ...] = Field(default_factory=tuple)

    @classmethod
    def from_sources(cls, *, env_override: dict[str, Any] | None = None) -> AppSettings:
        """Build settings from YAML files with optional environment overrides."""
        yaml_data = merge_configs(
            load_yaml_config("indicators.yaml"),
            load_yaml_config("risk.yaml"),
            load_yaml_config("execution.yaml"),
            load_yaml_config("connectors.yaml"),
            load_yaml_config("paper_adapter.yaml"),
            load_yaml_config("historical.yaml"),
            load_yaml_config("feature_flags.yaml"),
            load_yaml_config("markets.yaml"),
            load_yaml_config("logging.yaml"),
            load_yaml_config("monitoring.yaml"),
            load_yaml_config("services.yaml"),
            load_yaml_config("pipeline.yaml"),
            load_yaml_config("workflow.yaml"),
            load_yaml_config("data.yaml"),
            load_yaml_config("core.yaml"),
            load_yaml_config("ml.yaml"),
            load_yaml_config("ai.yaml"),
            load_yaml_config("decision.yaml"),
            load_yaml_config("plugins.yaml"),
            load_yaml_config("security.yaml"),
            load_yaml_config("notifications.yaml"),
        )
        if env_override:
            yaml_data = merge_configs(yaml_data, env_override)
        return cls(**_flatten_for_settings(yaml_data))

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        parts = value.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            msg = "schema_version must follow MAJOR.MINOR.PATCH format"
            raise ValueError(msg)
        return value


def _flatten_for_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Map merged YAML to AppSettings constructor kwargs."""
    allowed_keys = {
        "app_name",
        "environment",
        "schema_version",
        "logging",
        "monitoring",
        "services",
        "pipeline",
        "workflow",
        "data",
        "core",
        "ml",
        "ai",
        "decision",
        "plugins",
        "security",
        "notifications",
        "database",
        "redis",
        "indicators",
        "risk",
        "execution",
        "connectors",
        "paper_adapter",
        "historical",
        "feature_flags",
        "markets",
    }
    return {key: value for key, value in data.items() if key in allowed_keys}


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached application settings."""
    try:
        return AppSettings.from_sources()
    except (ConfigurationError, ValueError, TypeError) as error:
        msg = f"Failed to load application settings: {error}"
        raise ConfigurationError(msg) from error


def reset_settings() -> None:
    """Clear settings cache. Intended for tests."""
    get_settings.cache_clear()
