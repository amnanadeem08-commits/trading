"""Feature store validator."""

from __future__ import annotations

from feature_store.models.feature_dataset import FeatureDataset
from feature_store.models.feature_record import FeatureRecord
from feature_store.validation.validation_result import ValidationResult


class FeatureStoreValidator:
    """Validates feature datasets and records."""

    def validate_record(self, record: FeatureRecord | None) -> ValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        checks["record_present"] = record is not None
        if record is None:
            errors.append("Feature record is required")
            return ValidationResult(valid=False, checks=checks, errors=tuple(errors))
        checks["record_id_present"] = bool(record.record_id.strip())
        checks["dataset_id_present"] = bool(record.dataset_id.strip())
        checks["values_present"] = len(record.values) > 0
        if not checks["values_present"]:
            errors.append("Feature record must contain values")
        return ValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_records(self, records: tuple[FeatureRecord, ...]) -> ValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        seen: set[str] = set()
        duplicate = False
        for record in records:
            if record.record_id in seen:
                duplicate = True
                break
            seen.add(record.record_id)
            result = self.validate_record(record)
            if not result.valid:
                errors.extend(result.errors)
        checks["no_duplicates"] = not duplicate
        if duplicate:
            errors.append("Duplicate record ids detected")
        return ValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_dataset(
        self,
        dataset: FeatureDataset,
        *,
        records: tuple[FeatureRecord, ...],
    ) -> ValidationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []
        checks["dataset_id_present"] = bool(dataset.dataset_id.strip())
        checks["checksum_present"] = bool(dataset.checksum) or len(records) == 0
        checks["record_count_match"] = dataset.record_count == len(records)
        if not checks["record_count_match"]:
            errors.append("Record count mismatch")
        record_result = self.validate_records(records)
        checks.update(record_result.checks)
        errors.extend(record_result.errors)
        return ValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_checksum(
        self,
        dataset: FeatureDataset,
        *,
        records: tuple[FeatureRecord, ...],
    ) -> ValidationResult:
        from feature_store.models.feature_dataset import compute_feature_dataset_hash

        computed = compute_feature_dataset_hash(tuple(item.values for item in records))
        valid = computed == dataset.checksum
        checks = {"checksum_match": valid}
        errors = () if valid else ("Checksum mismatch",)
        return ValidationResult(valid=valid, checks=checks, errors=errors)
