"""Dataset domain contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from data.metadata import DatasetMetadata
from data.schema import DatasetSchema
from data.state import DatasetState
from models.common import PlatformModel


class Dataset(PlatformModel):
    """Registered dataset definition."""

    dataset_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    dataset_schema: DatasetSchema
    metadata: DatasetMetadata
    state: DatasetState = DatasetState.REGISTERED
    dependencies: tuple[str, ...] = Field(default_factory=tuple)


class BaseDataset(ABC):
    """Executable dataset implementation contract."""

    @abstractmethod
    def dataset_id(self) -> str:
        """Return the dataset identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the dataset display name."""

    @abstractmethod
    def version(self) -> str:
        """Return the dataset version."""

    @abstractmethod
    def schema(self) -> DatasetSchema:
        """Return the dataset schema."""

    def dependencies(self) -> tuple[str, ...]:
        """Return dataset identifiers this dataset depends on."""
        return ()

    def metadata(self) -> DatasetMetadata:
        """Return dataset metadata."""
        return DatasetMetadata(
            dataset_id=self.dataset_id(),
            name=self.name(),
            version=self.version(),
        )

    def to_definition(self, *, state: DatasetState = DatasetState.REGISTERED) -> Dataset:
        """Convert the dataset implementation to a registered definition."""
        return Dataset(
            dataset_id=self.dataset_id(),
            name=self.name(),
            version=self.version(),
            dataset_schema=self.schema(),
            metadata=self.metadata(),
            state=state,
            dependencies=self.dependencies(),
        )

    @abstractmethod
    def load(self) -> tuple[dict[str, Any], ...]:
        """Load dataset records."""

    def transform(self, records: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        """Transform loaded records. Default is identity."""
        return records
