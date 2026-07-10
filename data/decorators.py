"""Dataset registration decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from data.dataset import BaseDataset

DatasetType = TypeVar("DatasetType", bound=type[BaseDataset])

_DATASET_METADATA_KEY = "_platform_dataset_metadata"


def dataset(
    *,
    dataset_id: str | None = None,
    auto_register: bool = True,
) -> Callable[[DatasetType], DatasetType]:
    """Attach discovery metadata to a dataset implementation."""

    def decorator(defn: DatasetType) -> DatasetType:
        setattr(
            defn,
            _DATASET_METADATA_KEY,
            {
                "dataset_id": dataset_id,
                "auto_register": auto_register,
            },
        )
        return defn

    return decorator


def dataset_metadata(defn: type[BaseDataset] | BaseDataset) -> dict[str, str | bool | None]:
    """Return discovery metadata attached to a dataset implementation."""
    metadata = getattr(defn, _DATASET_METADATA_KEY, None)
    if metadata is None:
        return {"dataset_id": None, "auto_register": False}
    return dict(metadata)
