"""Dataset metadata serialization."""

from __future__ import annotations

from typing import Any

from data.metadata import DatasetMetadata


def serialize_metadata(metadata: DatasetMetadata) -> str:
    """Serialize dataset metadata to a JSON string."""
    return metadata.model_dump_json()


def deserialize_metadata(payload: str | dict[str, Any]) -> DatasetMetadata:
    """Deserialize dataset metadata from JSON or a mapping."""
    if isinstance(payload, str):
        return DatasetMetadata.model_validate_json(payload)
    return DatasetMetadata.model_validate(payload)
