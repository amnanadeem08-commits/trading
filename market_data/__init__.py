"""Market data framework public API."""

from market_data.exceptions import (
    MarketDataError,
    MarketNormalizationError,
    MarketRecordNotFoundError,
    MarketRegistrationError,
    MarketValidationError,
    MarketVersionError,
    StreamError,
)
from market_data.integration.historical_bridge import (
    build_stream_from_repository,
    market_record_from_historical,
    records_from_repository,
    register_from_repository,
    register_version_from_repository,
)
from market_data.lifecycle.market_lifecycle import (
    MarketLifecycleEvent,
    MarketLifecycleEventType,
    MarketLifecycleManager,
)
from market_data.models.candle import Candle
from market_data.models.event_record import EventRecord
from market_data.models.market_record import MarketRecord, MarketRecordType
from market_data.models.orderbook_snapshot import BookLevel, OrderBookSnapshot
from market_data.models.quote import Quote
from market_data.models.tick import Tick
from market_data.registry.market_catalog import MarketCatalogEntry
from market_data.registry.market_registry import (
    MarketDataRegistry,
    get_market_data_registry,
    reset_market_data_registry,
)
from market_data.schema.normalization import (
    map_fields,
    normalize_candle_payload,
    normalize_event_payload,
    normalize_historical_payload,
    normalize_orderbook_payload,
    normalize_quote_payload,
    normalize_tick_payload,
    normalize_timestamp,
    schema_for_record_type,
)
from market_data.schema.schema import MarketSchema
from market_data.schema.validator import MarketSchemaValidator, MarketValidationResult
from market_data.stream.stream_batch import StreamBatch
from market_data.stream.stream_buffer import StreamBuffer
from market_data.stream.stream_context import StreamContext
from market_data.stream.stream_result import StreamResult
from market_data.versioning.market_version import MarketVersion, MarketVersionRegistry

__all__ = [
    "BookLevel",
    "Candle",
    "EventRecord",
    "MarketCatalogEntry",
    "MarketDataError",
    "MarketDataRegistry",
    "MarketLifecycleEvent",
    "MarketLifecycleEventType",
    "MarketLifecycleManager",
    "MarketNormalizationError",
    "MarketRecord",
    "MarketRecordNotFoundError",
    "MarketRecordType",
    "MarketRegistrationError",
    "MarketSchema",
    "MarketSchemaValidator",
    "MarketValidationError",
    "MarketValidationResult",
    "MarketVersion",
    "MarketVersionError",
    "MarketVersionRegistry",
    "OrderBookSnapshot",
    "Quote",
    "StreamBatch",
    "StreamBuffer",
    "StreamContext",
    "StreamError",
    "StreamResult",
    "Tick",
    "build_stream_from_repository",
    "get_market_data_registry",
    "map_fields",
    "market_record_from_historical",
    "normalize_candle_payload",
    "normalize_event_payload",
    "normalize_historical_payload",
    "normalize_orderbook_payload",
    "normalize_quote_payload",
    "normalize_tick_payload",
    "normalize_timestamp",
    "records_from_repository",
    "register_from_repository",
    "register_version_from_repository",
    "reset_market_data_registry",
    "schema_for_record_type",
]
