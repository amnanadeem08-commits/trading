"""Historical query request contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from historical.query.filters import QueryFilters
from models.common import PlatformModel


class QueryType(StrEnum):
    """Supported historical query types."""

    BY_ID = "by_id"
    BY_VERSION = "by_version"
    TIME_RANGE = "time_range"
    METADATA = "metadata"
    TAG = "tag"
    CURSOR = "cursor"


class QueryRequest(PlatformModel):
    """Request for a historical query operation."""

    query_type: QueryType
    filters: QueryFilters = Field(default_factory=QueryFilters)
