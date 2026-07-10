"""Historical repository bridge for market data normalization."""

from __future__ import annotations

from historical.storage.repository import Repository
from historical.storage.repository_record import RepositoryRecord
from market_data.models.market_record import MarketRecord, MarketRecordType
from market_data.registry.market_catalog import MarketCatalogEntry
from market_data.registry.market_registry import MarketDataRegistry
from market_data.schema.normalization import normalize_historical_payload
from market_data.stream.stream_buffer import StreamBuffer
from market_data.stream.stream_context import StreamContext
from market_data.versioning.market_version import MarketVersion, MarketVersionRegistry


def records_from_repository(
    repository: Repository,
    *,
    dataset_id: str,
    symbol_id: str,
    record_type: MarketRecordType = MarketRecordType.CANDLE,
) -> tuple[MarketRecord, ...]:
    """Load and normalize historical repository records into market records."""
    historical_records = repository.load(dataset_id)
    normalized: list[MarketRecord] = []
    for item in historical_records:
        normalized.append(
            normalize_historical_payload(
                record_id=item.record_id,
                dataset_id=dataset_id,
                symbol_id=symbol_id,
                payload=dict(item.payload),
                sequence=item.sequence,
                record_type=record_type,
            )
        )
    return tuple(normalized)


def register_from_repository(
    repository: Repository,
    registry: MarketDataRegistry,
    *,
    dataset_id: str,
    symbol_id: str,
    name: str,
    record_type: MarketRecordType = MarketRecordType.CANDLE,
    capabilities: tuple[str, ...] = ("normalize", "stream"),
) -> MarketCatalogEntry:
    """Register a market catalog entry from a historical dataset."""
    dataset = repository.get_dataset(dataset_id)
    entry = MarketCatalogEntry(
        dataset_id=dataset_id,
        name=name,
        version=dataset.version,
        record_type=record_type,
        symbol_id=symbol_id,
        source_id=dataset.source,
        capabilities=capabilities,
        tags=dataset.tags,
    )
    registry.register(entry)
    return entry


def build_stream_from_repository(
    repository: Repository,
    *,
    dataset_id: str,
    symbol_id: str,
    stream_id: str = "market-stream",
    buffer_size: int = 100,
    batch_size: int = 10,
    record_type: MarketRecordType = MarketRecordType.CANDLE,
) -> StreamBuffer:
    """Build a stream buffer from historical repository records."""
    records = records_from_repository(
        repository,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        record_type=record_type,
    )
    context = StreamContext(
        stream_id=stream_id,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        buffer_size=max(buffer_size, len(records)),
        batch_size=batch_size,
    )
    return StreamBuffer(context, records)


def register_version_from_repository(
    repository: Repository,
    version_registry: MarketVersionRegistry,
    *,
    dataset_id: str,
) -> MarketVersion:
    """Register version metadata from a historical dataset."""
    version = repository.version(dataset_id)
    market_version = MarketVersion(
        dataset_id=dataset_id,
        version=version.version,
        description=version.description,
        snapshot_id=version.snapshot_id,
    )
    version_registry.register(market_version)
    return market_version


def market_record_from_historical(record: RepositoryRecord, *, symbol_id: str) -> MarketRecord:
    """Normalize a single historical repository record."""
    return normalize_historical_payload(
        record_id=record.record_id,
        dataset_id=record.dataset_id,
        symbol_id=symbol_id,
        payload=dict(record.payload),
        sequence=record.sequence,
    )
