"""Dataset schema definitions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from models.common import PlatformModel


class SchemaField(PlatformModel):
    """Single field in a dataset schema."""

    name: str = Field(min_length=1)
    field_type: Literal["string", "integer", "float", "boolean", "datetime", "object"] = "string"
    required: bool = True
    nullable: bool = False
    description: str = ""


class DatasetSchema(PlatformModel):
    """Schema contract for a dataset."""

    schema_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    fields: tuple[SchemaField, ...] = Field(default_factory=tuple)
    description: str = ""

    def field_names(self) -> tuple[str, ...]:
        """Return ordered field names."""
        return tuple(field.name for field in self.fields)

    def required_fields(self) -> tuple[str, ...]:
        """Return names of required fields."""
        return tuple(field.name for field in self.fields if field.required)

    def validate_record(self, record: dict[str, Any]) -> tuple[str, ...]:
        """Validate a record against this schema. Returns validation errors."""
        errors: list[str] = []
        for field in self.fields:
            if field.name not in record:
                if field.required:
                    errors.append(f"Missing required field: {field.name}")
                continue
            value = record[field.name]
            if value is None:
                if not field.nullable:
                    errors.append(f"Field '{field.name}' must not be null")
                continue
            if not _value_matches_type(value, field.field_type):
                errors.append(
                    f"Field '{field.name}' expected type '{field.field_type}', "
                    f"got '{type(value).__name__}'"
                )
        return tuple(errors)


def _value_matches_type(value: Any, field_type: str) -> bool:
    if field_type == "string":
        return isinstance(value, str)
    if field_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if field_type == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if field_type == "boolean":
        return isinstance(value, bool)
    if field_type == "datetime":
        return isinstance(value, str)
    if field_type == "object":
        return isinstance(value, dict)
    return False
