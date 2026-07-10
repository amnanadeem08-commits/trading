"""Dataset selector consuming feature store only."""

from __future__ import annotations

from feature_store.exceptions import DatasetNotFoundError, SnapshotNotFoundError
from feature_store.models.feature_dataset import FeatureDataset
from feature_store.storage.feature_store import FeatureStore
from models.common import utc_now
from training_pipeline.datasets.dataset_reference import DatasetReference
from training_pipeline.datasets.dataset_snapshot import DatasetSnapshot
from training_pipeline.exceptions import DatasetReferenceError


class DatasetSelector:
    """Selects training datasets from the feature store."""

    def __init__(self, store: FeatureStore) -> None:
        self._store = store

    def resolve_reference(
        self,
        *,
        dataset_id: str,
        version: str | None = None,
        snapshot_id: str | None = None,
    ) -> DatasetReference:
        try:
            dataset = self._store.repository.get_dataset(dataset_id)
        except DatasetNotFoundError as error:
            raise DatasetReferenceError(str(error)) from error

        resolved_version = version or dataset.version
        record_count = dataset.record_count
        checksum = dataset.checksum

        if snapshot_id is not None:
            try:
                snapshot = self._store.repository.get_snapshot(snapshot_id)
            except SnapshotNotFoundError as error:
                raise DatasetReferenceError(str(error)) from error
            if snapshot.dataset_id != dataset_id:
                msg = f"Snapshot {snapshot_id} does not belong to dataset {dataset_id}"
                raise DatasetReferenceError(msg)
            record_count = snapshot.record_count
            checksum = snapshot.checksum
            resolved_version = snapshot.version

        return DatasetReference(
            dataset_id=dataset_id,
            version=resolved_version,
            snapshot_id=snapshot_id,
            record_count=record_count,
            checksum=checksum,
        )

    def capture_snapshot(self, dataset_id: str) -> DatasetSnapshot:
        try:
            self._store.repository.get_dataset(dataset_id)
        except DatasetNotFoundError as error:
            raise DatasetReferenceError(str(error)) from error
        snapshot = self._store.create_snapshot(dataset_id)
        return DatasetSnapshot(
            snapshot_id=snapshot.snapshot_id,
            dataset_id=snapshot.dataset_id,
            version=snapshot.version,
            record_count=snapshot.record_count,
            checksum=snapshot.checksum,
            captured_at=utc_now(),
        )

    def list_available(self) -> tuple[FeatureDataset, ...]:
        dataset_ids = self._store.dataset_registry.list()
        return tuple(self._store.repository.get_dataset(dataset_id) for dataset_id in dataset_ids)
