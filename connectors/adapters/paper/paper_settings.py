"""Paper adapter configuration."""

from __future__ import annotations

from pydantic import Field, model_validator

from models.common import PlatformModel


class PaperSettings(PlatformModel):
    """Runtime settings for the paper execution adapter."""

    enabled: bool = True
    deterministic: bool = True
    random_seed: int = 42
    failure_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    latency_ms_min: int = Field(ge=0, default=1)
    latency_ms_max: int = Field(ge=0, default=50)
    simulate_delay: bool = False

    @model_validator(mode="after")
    def validate_latency_bounds(self) -> PaperSettings:
        if self.latency_ms_max < self.latency_ms_min:
            msg = "latency_ms_max must be greater than or equal to latency_ms_min"
            raise ValueError(msg)
        return self
