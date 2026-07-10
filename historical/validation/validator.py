"""Historical data validator."""

from __future__ import annotations

from historical.datasets.historical_dataset import HistoricalDataset, compute_dataset_checksum
from historical.storage.repository_record import RepositoryRecord
from historical.validation.validation_result import HistoricalValidationResult


class HistoricalValidator:
    """Validates historical datasets, records, and versions."""

    def validate_dataset(self, dataset: HistoricalDataset | None) -> HistoricalValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        checks["dataset_present"] = dataset is not None
        if dataset is None:
            errors.append("Dataset is required")
            return HistoricalValidationResult(valid=False, checks=checks, errors=tuple(errors))
        checks["dataset_id_present"] = bool(dataset.dataset_id.strip())
        checks["version_present"] = bool(dataset.version.strip())
        if not checks["dataset_id_present"]:
            errors.append("Dataset id is required")
        if not checks["version_present"]:
            errors.append("Dataset version is required")
        checks["record_count_valid"] = dataset.record_count >= 0
        return HistoricalValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_schema(
        self,
        dataset: HistoricalDataset,
        record: RepositoryRecord,
    ) -> HistoricalValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        for field_name in dataset.dataset_schema.required_fields:
            present = field_name in record.payload
            checks[f"field_{field_name}"] = present
            if not present:
                errors.append(f"Missing required field: {field_name}")
        timestamp_field = dataset.dataset_schema.timestamp_field
        checks["timestamp_present"] = (
            timestamp_field in record.payload or record.timestamp is not None
        )
        return HistoricalValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_timestamps(
        self,
        records: tuple[RepositoryRecord, ...],
    ) -> HistoricalValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        previous = None
        monotonic = True
        for record in records:
            if previous is not None and record.timestamp < previous:
                monotonic = False
                break
            previous = record.timestamp
        checks["timestamps_monotonic"] = monotonic
        if not monotonic:
            errors.append("Record timestamps must be monotonic")
        return HistoricalValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_duplicates(
        self,
        records: tuple[RepositoryRecord, ...],
    ) -> HistoricalValidationResult:
        seen: set[str] = set()
        duplicate = False
        for record in records:
            if record.record_id in seen:
                duplicate = True
                break
            seen.add(record.record_id)
        checks = {"no_duplicates": not duplicate}
        errors = ["Duplicate record ids detected"] if duplicate else []
        return HistoricalValidationResult(valid=not duplicate, checks=checks, errors=tuple(errors))

    def validate_checksum(
        self,
        dataset: HistoricalDataset,
        records: tuple[RepositoryRecord, ...],
    ) -> HistoricalValidationResult:
        if not dataset.checksum:
            return HistoricalValidationResult(valid=True, checks={"checksum_present": False})
        computed = compute_dataset_checksum(tuple(item.payload for item in records))
        valid = computed == dataset.checksum
        checks = {"checksum_valid": valid}
        errors = [] if valid else ["Dataset checksum mismatch"]
        return HistoricalValidationResult(valid=valid, checks=checks, errors=tuple(errors))

    def validate_metadata(self, dataset: HistoricalDataset) -> HistoricalValidationResult:
        checks = {
            "metadata_present": dataset.metadata is not None,
            "metadata_id_matches": dataset.metadata.dataset_id == dataset.dataset_id,
        }
        errors = []
        if not checks["metadata_id_matches"]:
            errors.append("Metadata dataset id mismatch")
        return HistoricalValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_all(
        self,
        dataset: HistoricalDataset,
        records: tuple[RepositoryRecord, ...],
    ) -> HistoricalValidationResult:
        results = [
            self.validate_dataset(dataset),
            self.validate_metadata(dataset),
            self.validate_timestamps(records),
            self.validate_duplicates(records),
            self.validate_checksum(dataset, records),
        ]
        for record in records:
            results.append(self.validate_schema(dataset, record))
        checks: dict[str, bool] = {}
        errors: list[str] = []
        for result in results:
            checks.update(result.checks)
            errors.extend(result.errors)
        return HistoricalValidationResult(valid=not errors, checks=checks, errors=tuple(errors))
