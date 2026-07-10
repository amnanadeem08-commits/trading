"""Feature engineering bridge for feature store ingestion."""

from __future__ import annotations

from uuid import uuid4

from feature_engineering.models.feature_set import FeatureSet
from feature_engineering.models.feature_vector import FeatureVector
from feature_store.models.feature_dataset import FeatureDataset
from feature_store.models.feature_metadata import FeatureMetadata
from feature_store.models.feature_record import FeatureRecord
from feature_store.registry.feature_registry import FeatureRegistry, FeatureRegistryEntry
from feature_store.storage.feature_store import FeatureStore


def record_from_vector(vector: FeatureVector) -> FeatureRecord:
    """Convert a feature vector into a feature store record."""
    values = {feature.name: str(feature.value) for feature in vector.features}
    return FeatureRecord(
        record_id=f"fs-{vector.vector_id}",
        dataset_id=vector.dataset_id,
        symbol_id=vector.symbol_id,
        vector_id=vector.vector_id,
        source_record_id=vector.record_id,
        version=vector.version,
        timestamp=vector.timestamp,
        sequence=vector.sequence,
        values=values,
    )


def records_from_feature_set(feature_set: FeatureSet) -> tuple[FeatureRecord, ...]:
    """Convert a feature set into feature store records."""
    return tuple(record_from_vector(vector) for vector in feature_set.vectors)


def dataset_from_feature_set(feature_set: FeatureSet) -> FeatureDataset:
    """Build a feature dataset definition from a feature set."""
    metadata = FeatureMetadata(
        dataset_id=feature_set.metadata.dataset_id,
        name=feature_set.feature_set_id,
        schema_id=feature_set.metadata.schema_id,
        symbol_id=feature_set.metadata.symbol_id,
        version=feature_set.metadata.version,
        source_pipeline=feature_set.metadata.extractor_id,
        lineage=(feature_set.metadata.dataset_id,),
        tags=feature_set.metadata.tags,
    )
    return FeatureDataset(
        dataset_id=feature_set.metadata.dataset_id,
        version=feature_set.metadata.version,
        metadata=metadata,
        lineage=(feature_set.metadata.dataset_id, feature_set.metadata.extractor_id),
        tags=feature_set.metadata.tags,
    )


def register_features_from_set(
    feature_set: FeatureSet,
    registry: FeatureRegistry,
) -> tuple[FeatureRegistryEntry, ...]:
    """Register feature definitions from a feature set."""
    entries: list[FeatureRegistryEntry] = []
    if not feature_set.vectors:
        return ()
    for feature in feature_set.vectors[0].features:
        entry = FeatureRegistryEntry(
            feature_name=feature.name,
            dataset_id=feature_set.metadata.dataset_id,
            schema_id=feature_set.metadata.schema_id,
            dtype=feature.dtype,
            tags=("stored",),
        )
        registry.register(entry)
        entries.append(entry)
    return tuple(entries)


def ingest_feature_set(store: FeatureStore, feature_set: FeatureSet) -> FeatureDataset:
    """Register and ingest a feature set into the feature store."""
    dataset = dataset_from_feature_set(feature_set)
    store.register_dataset(dataset)
    records = records_from_feature_set(feature_set)
    store.ingest_records(records)
    register_features_from_set(feature_set, store.feature_registry)
    return store.repository.get_dataset(dataset.dataset_id)


def build_reproducible_dataset(
    store: FeatureStore,
    feature_set: FeatureSet,
    *,
    dataset_id: str | None = None,
) -> FeatureDataset:
    """Create a reproducible dataset with deterministic record ids."""
    resolved_id = dataset_id or feature_set.metadata.dataset_id
    records: list[FeatureRecord] = []
    for index, vector in enumerate(feature_set.vectors):
        record = record_from_vector(vector)
        records.append(
            record.model_copy(
                update={
                    "record_id": f"repro-{resolved_id}-{index}",
                    "dataset_id": resolved_id,
                }
            )
        )
    metadata = FeatureMetadata(
        dataset_id=resolved_id,
        name=feature_set.feature_set_id,
        schema_id=feature_set.metadata.schema_id,
        symbol_id=feature_set.metadata.symbol_id,
        version=feature_set.metadata.version,
        source_pipeline=feature_set.metadata.extractor_id,
        lineage=(feature_set.metadata.dataset_id, "reproducible"),
        tags=(*feature_set.metadata.tags, "reproducible"),
        attributes={"reproducibility_key": str(uuid4())},
    )
    dataset = FeatureDataset(
        dataset_id=resolved_id,
        version=feature_set.metadata.version,
        metadata=metadata,
        lineage=(feature_set.metadata.dataset_id, feature_set.metadata.extractor_id),
        tags=(*feature_set.metadata.tags, "reproducible"),
    )
    store.register_dataset(dataset)
    store.ingest_records(tuple(records))
    return store.repository.get_dataset(resolved_id)
