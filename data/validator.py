"""Schema validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data.exceptions import SchemaValidationError
from data.schema import DatasetSchema


@dataclass(frozen=True)
class SchemaValidationResult:
    """Outcome of schema record validation."""

    valid: bool
    errors: tuple[str, ...] = ()


class SchemaValidator:
    """Validates records against a dataset schema."""

    def __init__(self, schema: DatasetSchema) -> None:
        self._schema = schema

    @property
    def schema(self) -> DatasetSchema:
        return self._schema

    def validate_record(self, record: dict[str, Any]) -> SchemaValidationResult:
        """Validate a single record."""
        errors = self._schema.validate_record(record)
        return SchemaValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_records(self, records: tuple[dict[str, Any], ...]) -> SchemaValidationResult:
        """Validate multiple records."""
        all_errors: list[str] = []
        for index, record in enumerate(records):
            errors = self._schema.validate_record(record)
            for error in errors:
                all_errors.append(f"Record {index}: {error}")
        return SchemaValidationResult(valid=len(all_errors) == 0, errors=tuple(all_errors))

    def assert_valid(self, record: dict[str, Any]) -> None:
        """Raise SchemaValidationError when validation fails."""
        result = self.validate_record(record)
        if not result.valid:
            msg = "; ".join(result.errors)
            raise SchemaValidationError(msg)
