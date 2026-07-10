"""Connector layer public API."""

from connectors.adapters.adapter_context import AdapterContext
from connectors.adapters.adapter_metadata import (
    TERMINAL_ADAPTER_STATES,
    AdapterHealthResult,
    AdapterHealthStatus,
    AdapterMetadata,
    AdapterState,
)
from connectors.adapters.adapter_registry import (
    AdapterRegistry,
    get_adapter_registry,
    reset_adapter_registry,
)
from connectors.adapters.execution_adapter import ExecutionAdapter
from connectors.adapters.paper import (
    PAPER_ADAPTER_ID,
    TERMINAL_PAPER_STATES,
    PaperExecutionAdapter,
    PaperExecutionRecord,
    PaperExecutionResult,
    PaperSettings,
    PaperState,
)
from connectors.base import LiveSubscription, MarketConnector
from connectors.capabilities import ConnectorCapabilities, RateLimitInformation
from connectors.dispatch.dispatch_bridge import DispatchBridge
from connectors.dispatch.dispatch_request import ConnectorDispatchRequest
from connectors.dispatch.dispatch_response import DispatchResponse
from connectors.exceptions import (
    AdapterNotFoundError,
    AdapterRegistrationError,
    AdapterStateError,
    AuthenticationError,
    ConnectionError,
    ConnectorError,
    ConnectorNotFoundError,
    ConnectorOrchestrationError,
    ConnectorValidationError,
    DispatchBridgeError,
    NormalizationError,
    RateLimitError,
    UnsupportedCapabilityError,
)
from connectors.health import ConnectorHealthStatus, HealthCheckResult
from connectors.lifecycle.connector_lifecycle import (
    ConnectorDispatchRequestedEvent,
    ConnectorInitializedEvent,
    ConnectorLifecycleEvent,
    ConnectorLifecycleEventType,
    ConnectorLifecycleManager,
    ConnectorRegisteredEvent,
    ConnectorShutdownEvent,
    ConnectorValidatedEvent,
)
from connectors.market_registry import (
    ConnectorRegistry,
    get_connector_registry,
    reset_connector_registry,
)
from connectors.market_registry import (
    ConnectorRegistry as MarketConnectorRegistry,
)
from connectors.metadata import ConnectorMetadata
from connectors.normalizer import normalize_bar, normalize_bar_mapping, normalize_bars
from connectors.orchestration.connector_orchestrator import ConnectorOrchestrator
from connectors.registry.connector_registry import (
    ConnectorRecord,
    get_connector_framework_registry,
    reset_connector_framework_registry,
)
from connectors.registry.connector_registry import (
    ConnectorRegistry as ConnectorFrameworkRegistry,
)
from connectors.simulation import SimulationClock, SimulationEngine, SimulationIdGenerator
from connectors.validation.connector_validator import ConnectorValidator
from connectors.validation.paper_validator import PaperValidationResult, PaperValidator
from connectors.validation.validation_result import ConnectorValidationResult
from connectors.versioning.connector_version import ConnectorVersion

__all__ = [
    "PAPER_ADAPTER_ID",
    "TERMINAL_ADAPTER_STATES",
    "TERMINAL_PAPER_STATES",
    "AdapterContext",
    "AdapterHealthResult",
    "AdapterHealthStatus",
    "AdapterMetadata",
    "AdapterNotFoundError",
    "AdapterRegistrationError",
    "AdapterRegistry",
    "AdapterState",
    "AdapterStateError",
    "AuthenticationError",
    "ConnectionError",
    "ConnectorCapabilities",
    "ConnectorDispatchRequest",
    "ConnectorDispatchRequestedEvent",
    "ConnectorError",
    "ConnectorFrameworkRegistry",
    "ConnectorHealthStatus",
    "ConnectorInitializedEvent",
    "ConnectorLifecycleEvent",
    "ConnectorLifecycleEventType",
    "ConnectorLifecycleManager",
    "ConnectorMetadata",
    "ConnectorNotFoundError",
    "ConnectorOrchestrationError",
    "ConnectorOrchestrator",
    "ConnectorRecord",
    "ConnectorRegisteredEvent",
    "ConnectorRegistry",
    "ConnectorShutdownEvent",
    "ConnectorValidatedEvent",
    "ConnectorValidationError",
    "ConnectorValidationResult",
    "ConnectorValidator",
    "ConnectorVersion",
    "DispatchBridge",
    "DispatchBridgeError",
    "DispatchResponse",
    "ExecutionAdapter",
    "HealthCheckResult",
    "LiveSubscription",
    "MarketConnector",
    "MarketConnectorRegistry",
    "NormalizationError",
    "PaperExecutionAdapter",
    "PaperExecutionRecord",
    "PaperExecutionResult",
    "PaperSettings",
    "PaperState",
    "PaperValidationResult",
    "PaperValidator",
    "RateLimitError",
    "RateLimitInformation",
    "SimulationClock",
    "SimulationEngine",
    "SimulationIdGenerator",
    "UnsupportedCapabilityError",
    "get_adapter_registry",
    "get_connector_framework_registry",
    "get_connector_registry",
    "normalize_bar",
    "normalize_bar_mapping",
    "normalize_bars",
    "reset_adapter_registry",
    "reset_connector_framework_registry",
    "reset_connector_registry",
]
