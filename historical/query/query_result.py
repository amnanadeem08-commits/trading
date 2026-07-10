"""Historical query result contracts."""

from __future__ import annotations

from pydantic import Field

from historical.datasets.dataset_metadata import HistoricalDatasetMetadata
from historical.datasets.historical_dataset import HistoricalDataset
from historical.storage.repository_record import RepositoryRecord
from models.common import PlatformModel


class QueryResult(PlatformModel):
    """Outcome of a historical query operation."""

    matched: bool
    datasets: tuple[HistoricalDataset, ...] = Field(default_factory=tuple)
    records: tuple[RepositoryRecord, ...] = Field(default_factory=tuple)
    metadata: tuple[HistoricalDatasetMetadata, ...] = Field(default_factory=tuple)
    cursor_position: int | None = None
    total: int = 0
