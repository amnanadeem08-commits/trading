"""Feature schema registry."""

from __future__ import annotations

from threading import RLock

from feature_engineering.exceptions import FeatureSchemaError
from feature_engineering.schema.feature_schema import FeatureSchema


class FeatureSchemaRegistry:
    """Thread-safe registry for feature schemas."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._schemas: dict[str, FeatureSchema] = {}

    def register(self, schema: FeatureSchema) -> None:
        with self._lock:
            self._schemas[schema.schema_id] = schema

    def lookup(self, schema_id: str) -> FeatureSchema:
        with self._lock:
            schema = self._schemas.get(schema_id)
        if schema is None:
            msg = f"Schema not found: {schema_id}"
            raise FeatureSchemaError(msg)
        return schema

    def exists(self, schema_id: str) -> bool:
        with self._lock:
            return schema_id in self._schemas

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._schemas.keys()))
