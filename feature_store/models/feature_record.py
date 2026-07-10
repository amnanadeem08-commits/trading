"""Feature record contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class FeatureRecord(PlatformModel):
    """Stored feature record derived from a feature vector."""

    record_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    vector_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    version: str = Field(min_length=1, default="1.0.0")
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    sequence: int = Field(ge=0, default=0)
    values: dict[str, str] = Field(default_factory=dict)
