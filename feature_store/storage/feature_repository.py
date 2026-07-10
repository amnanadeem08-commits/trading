"""In-memory feature repository."""

from __future__ import annotations

from threading import RLock

from feature_store.exceptions import DatasetNotFoundError, FeatureRecordNotFoundError
from feature_store.models.feature_dataset import FeatureDataset, compute_feature_dataset_hash
from feature_store.models.feature_record import FeatureRecord
from feature_store.models.feature_snapshot import FeatureSnapshot


class FeatureRepository:
    """Coordinates feature dataset registration and record storage."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._datasets: dict[str, FeatureDataset] = {}
        self._records: dict[str, list[FeatureRecord]] = {}
        self._snapshots: dict[str, FeatureSnapshot] = {}

    def register_dataset(self, dataset: FeatureDataset) -> None:
        with self._lock:
            self._datasets[dataset.dataset_id] = dataset
            self._records.setdefault(dataset.dataset_id, [])

    def get_dataset(self, dataset_id: str) -> FeatureDataset:
        with self._lock:
            dataset = self._datasets.get(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id)
        return dataset

    def exists(self, dataset_id: str) -> bool:
        with self._lock:
            return dataset_id in self._datasets

    def list_datasets(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._datasets.keys()))

    def store(self, record: FeatureRecord) -> None:
        with self._lock:
            if record.dataset_id not in self._datasets:
                raise DatasetNotFoundError(record.dataset_id)
            records = self._records.setdefault(record.dataset_id, [])
            records.append(record)
            self._refresh_dataset(record.dataset_id)

    def store_many(self, records: tuple[FeatureRecord, ...]) -> None:
        for record in records:
            self.store(record)

    def load(self, dataset_id: str, *, version: str | None = None) -> tuple[FeatureRecord, ...]:
        with self._lock:
            if dataset_id not in self._datasets:
                raise DatasetNotFoundError(dataset_id)
            records = list(self._records.get(dataset_id, ()))
        if version is not None:
            records = [item for item in records if item.version == version]
        return tuple(records)

    def lookup(self, record_id: str, *, dataset_id: str) -> FeatureRecord:
        records = self.load(dataset_id)
        for record in records:
            if record.record_id == record_id:
                return record
        raise FeatureRecordNotFoundError(record_id)

    def delete(self, dataset_id: str) -> None:
        with self._lock:
            if dataset_id not in self._datasets:
                raise DatasetNotFoundError(dataset_id)
            del self._datasets[dataset_id]
            self._records.pop(dataset_id, None)

    def create_snapshot(self, dataset_id: str) -> FeatureSnapshot:
        with self._lock:
            dataset = self._datasets.get(dataset_id)
            if dataset is None:
                raise DatasetNotFoundError(dataset_id)
            snapshot = FeatureSnapshot(
                snapshot_id=f"snapshot-{dataset_id}-{dataset.version}",
                dataset_id=dataset_id,
                version=dataset.version,
                record_count=dataset.record_count,
                checksum=dataset.checksum,
                lineage=dataset.lineage,
            )
            self._snapshots[snapshot.snapshot_id] = snapshot
            return snapshot

    def get_snapshot(self, snapshot_id: str) -> FeatureSnapshot:
        with self._lock:
            snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            from feature_store.exceptions import SnapshotNotFoundError

            raise SnapshotNotFoundError(snapshot_id)
        return snapshot

    def list_snapshots(self, dataset_id: str) -> tuple[FeatureSnapshot, ...]:
        with self._lock:
            return tuple(item for item in self._snapshots.values() if item.dataset_id == dataset_id)

    def _refresh_dataset(self, dataset_id: str) -> None:
        records = self._records.get(dataset_id, [])
        dataset = self._datasets[dataset_id]
        checksum = compute_feature_dataset_hash(tuple(item.values for item in records))
        start = records[0].timestamp if records else None
        end = records[-1].timestamp if records else None
        updated = (
            dataset.with_record_count(len(records))
            .with_checksum(checksum)
            .with_time_range(start=start, end=end)
        )
        self._datasets[dataset_id] = updated
