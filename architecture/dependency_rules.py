"""Frozen architecture dependency and forbidden-import rules."""

from __future__ import annotations

from enum import IntEnum

# Pipeline layers ordered from lowest (foundation) to highest (execution).
# Higher layers may import lower layers. Reverse imports are forbidden.


class PipelineLayer(IntEnum):
    HISTORICAL = 0
    MARKET_DATA = 1
    FEATURE_ENGINEERING = 2
    CONNECTORS = 3
    DATA = 4
    CORE = 5
    FEATURE_STORE = 6
    TRAINING_PIPELINE = 7
    MODEL_REGISTRY = 8
    INFERENCE_PIPELINE = 9
    ML_RUNTIME = 10
    ML_ENGINE_PLUGINS = 11
    FRAMEWORK_ADAPTERS = 12
    ARTIFACT_MANAGEMENT = 13
    STORAGE_PROVIDERS = 14
    ML = 15
    AI = 16
    AGENTS = 17
    DECISION = 18
    RISK = 19
    EXECUTION = 20


PIPELINE_LAYER_ORDER: tuple[PipelineLayer, ...] = tuple(PipelineLayer)

PIPELINE_PACKAGES: dict[str, PipelineLayer] = {
    "historical": PipelineLayer.HISTORICAL,
    "market_data": PipelineLayer.MARKET_DATA,
    "feature_engineering": PipelineLayer.FEATURE_ENGINEERING,
    "connectors": PipelineLayer.CONNECTORS,
    "data": PipelineLayer.DATA,
    "core": PipelineLayer.CORE,
    "feature_store": PipelineLayer.FEATURE_STORE,
    "training_pipeline": PipelineLayer.TRAINING_PIPELINE,
    "model_registry": PipelineLayer.MODEL_REGISTRY,
    "inference_pipeline": PipelineLayer.INFERENCE_PIPELINE,
    "ml_runtime": PipelineLayer.ML_RUNTIME,
    "ml_engine_plugins": PipelineLayer.ML_ENGINE_PLUGINS,
    "framework_adapters": PipelineLayer.FRAMEWORK_ADAPTERS,
    "artifact_management": PipelineLayer.ARTIFACT_MANAGEMENT,
    "storage_providers": PipelineLayer.STORAGE_PROVIDERS,
    "ml": PipelineLayer.ML,
    "ai": PipelineLayer.AI,
    "agents": PipelineLayer.AGENTS,
    "decision": PipelineLayer.DECISION,
    "risk": PipelineLayer.RISK,
    "execution": PipelineLayer.EXECUTION,
}

# import-linter layers contract uses highest-first ordering.
IMPORT_LINTER_LAYERS: tuple[str, ...] = tuple(reversed(list(PIPELINE_PACKAGES.keys())))

FOUNDATION_PACKAGES: frozenset[str] = frozenset(
    {
        "models",
        "config",
        "events",
        "versioning",
        "audit",
        "feature_flags",
        "architecture",
        "health",
        "metrics",
        "platform_logging",
        "security",
        "notifications",
        "monitoring",
    }
)

PRODUCTION_PACKAGES: frozenset[str] = frozenset(FOUNDATION_PACKAGES | set(PIPELINE_PACKAGES.keys()))

GOVERNANCE_PACKAGES: frozenset[str] = frozenset(
    {
        "events",
        "versioning",
        "audit",
        "feature_flags",
    }
)

PRESENTATION_PACKAGES: frozenset[str] = frozenset({"dashboard", "api"})

SERVICE_PACKAGES: frozenset[str] = frozenset({"services"})

ORCHESTRATION_PACKAGES: frozenset[str] = frozenset({"pipeline", "workflow", "plugins"})

RESEARCH_PACKAGE = "research"

# Pre-Phase-0 modules excluded until migration is complete.
LEGACY_PATH_PREFIXES: tuple[str, ...] = (
    "main.py",
    "dashboard.py",
    "config.py",
    "core/indicators.py",
    "core/sentiment.py",
    "core/llm_analyzer.py",
    "connectors/binance_connector.py",
    "connectors/psx_connector.py",
    "tests/test_llm_analyzer.py",
)

LEGACY_CONNECTOR_FILES: frozenset[str] = frozenset(
    {
        "connectors/binance_connector.py",
        "connectors/psx_connector.py",
    }
)

# Explicit forbidden import pairs: source package -> forbidden target roots.
FORBIDDEN_IMPORT_PAIRS: dict[str, frozenset[str]] = {
    "services": frozenset({"connectors"}),
    "pipeline": frozenset(
        {
            "connectors",
            "ml",
            "ai",
            "risk",
            "execution",
            "api",
            "dashboard",
        }
    ),
    "workflow": frozenset(
        {
            "connectors",
            "ml",
            "ai",
            "risk",
            "execution",
            "api",
            "dashboard",
        }
    ),
    "plugins": frozenset(
        {
            "connectors",
            "ml",
            "ai",
            "llm",
            "risk",
            "execution",
            "api",
            "dashboard",
        }
    ),
    "data": frozenset(
        {
            "feature_store",
            "training_pipeline",
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "connectors",
            "core",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "api",
            "dashboard",
            "research",
        }
    ),
    "core": frozenset(
        {
            "feature_store",
            "training_pipeline",
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ai",
            "connectors",
            "ml",
            "llm",
            "decision",
            "risk",
            "execution",
            "api",
            "dashboard",
            "research",
        }
    ),
    "feature_store": frozenset(
        {
            "training_pipeline",
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "training_pipeline": frozenset(
        {
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "model_registry": frozenset(
        {
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "inference_pipeline": frozenset(
        {
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "ml_runtime": frozenset(
        {
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "ml_engine_plugins": frozenset(
        {
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "framework_adapters": frozenset(
        {
            "artifact_management",
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "artifact_management": frozenset(
        {
            "storage_providers",
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "storage_providers": frozenset(
        {
            "ml",
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "ml": frozenset(
        {
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    ),
    "ai": frozenset(
        {
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    ),
    "decision": frozenset(
        {
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    ),
    "risk": frozenset(
        {
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    ),
    "execution": frozenset(
        {
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    ),
    "historical": frozenset(
        {
            "market_data",
            "feature_engineering",
            "feature_store",
            "training_pipeline",
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "connectors",
            "core",
            "ml",
            "ai",
            "decision",
            "risk",
            "execution",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "market_data": frozenset(
        {
            "feature_engineering",
            "feature_store",
            "training_pipeline",
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "connectors",
            "core",
            "ml",
            "ai",
            "decision",
            "risk",
            "execution",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "feature_engineering": frozenset(
        {
            "feature_store",
            "training_pipeline",
            "model_registry",
            "inference_pipeline",
            "ml_runtime",
            "ml_engine_plugins",
            "framework_adapters",
            "artifact_management",
            "storage_providers",
            "connectors",
            "core",
            "ml",
            "ai",
            "decision",
            "risk",
            "execution",
            "api",
            "dashboard",
            "research",
            "services",
            "pipeline",
            "workflow",
        }
    ),
    "connectors": frozenset(
        {
            "services",
            "pipeline",
            "workflow",
            "dashboard",
            "api",
            "research",
        }
    ),
    "dashboard": frozenset(
        {
            "connectors",
            "data",
            "core",
            "ml",
            "ai",
            "agents",
            "decision",
            "risk",
            "execution",
        }
    ),
    "api": frozenset({RESEARCH_PACKAGE}),
}

# Packages that must never import research.
RESEARCH_FORBIDDEN_SOURCES: frozenset[str] = PRODUCTION_PACKAGES | frozenset(
    {
        "api",
        "dashboard",
        "services",
        "pipeline",
        "workflow",
        "plugins",
        "data",
        "historical",
        "market_data",
        "feature_engineering",
        "feature_store",
        "training_pipeline",
        "model_registry",
        "inference_pipeline",
        "ml_runtime",
        "ml_engine_plugins",
        "core",
        "ml",
        "ai",
        "decision",
        "risk",
        "execution",
    }
)

# Connector framework may import upstream intelligence layers to bridge execution.
CONNECTOR_BRIDGE_IMPORTS: frozenset[str] = frozenset(
    {
        "historical",
        "market_data",
        "feature_engineering",
        "feature_store",
        "data",
        "core",
        "ml",
        "ai",
        "decision",
        "risk",
        "execution",
        "plugins",
    }
)

# Connectors must not depend on service or presentation layers.
CONNECTOR_FORBIDDEN_IMPORTS: frozenset[str] = frozenset(
    {
        "services",
        "pipeline",
        "workflow",
        "dashboard",
        "api",
        "research",
    }
)

# Upper foundation layers must not import connectors directly.
CONNECTOR_IMPORT_FORBIDDEN_SOURCES: frozenset[str] = frozenset(
    {
        "models",
        "config",
        "events",
        "versioning",
        "audit",
        "feature_flags",
        "architecture",
        "health",
        "metrics",
        "platform_logging",
        "security",
        "notifications",
        "monitoring",
    }
)

# Governance packages must not import pipeline or service layers.
GOVERNANCE_FORBIDDEN_IMPORTS: frozenset[str] = frozenset(
    {
        "services",
        "core",
        "ml",
        "ai",
        "agents",
        "decision",
        "strategy",
        "risk",
        "data",
        "api",
        "connectors",
        "research",
    }
)

# Research may only depend on models and stdlib-style modules.
RESEARCH_ALLOWED_IMPORTS: frozenset[str] = frozenset(
    {
        "__future__",
        "models",
        "abc",
        "enum",
        "typing",
        "research",
    }
)

STDLIB_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "__future__",
        "abc",
        "ast",
        "collections",
        "dataclasses",
        "datetime",
        "enum",
        "functools",
        "io",
        "json",
        "pathlib",
        "re",
        "sys",
        "threading",
        "typing",
        "uuid",
    }
)

MARKET_BRANCHING_IDENTIFIERS: frozenset[str] = frozenset({"market", "exchange"})

MARKET_BRANCHING_STRINGS: frozenset[str] = frozenset(
    {
        "binance",
        "pmex",
        "psx",
        "crypto",
        "bybit",
        "okx",
    }
)

MARKET_BRANCHING_SUBSTRINGS: frozenset[str] = frozenset({":", "market", "exchange"})

RULE_IDS: dict[str, str] = {
    "dependency_direction": "R11",
    "forbidden_import": "R11",
    "research_isolation": "R9",
    "service_boundary": "R3",
    "pipeline_boundary": "R3",
    "workflow_boundary": "R3",
    "plugins_boundary": "R3",
    "data_boundary": "R11",
    "core_boundary": "R11",
    "ml_boundary": "R11",
    "ai_boundary": "R11",
    "decision_boundary": "R11",
    "risk_boundary": "R11",
    "execution_boundary": "R11",
    "connector_boundary": "R10",
    "feature_engineering_boundary": "R11",
    "feature_store_boundary": "R11",
    "training_pipeline_boundary": "R11",
    "model_registry_boundary": "R11",
    "inference_pipeline_boundary": "R11",
    "ml_runtime_boundary": "R11",
    "ml_engine_plugins_boundary": "R11",
    "framework_adapters_boundary": "R11",
    "artifact_management_boundary": "R11",
    "storage_providers_boundary": "R11",
    "layer_rule": "R11",
    "presentation_boundary": "R12",
}
