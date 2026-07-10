"""Experiment metrics container."""

from __future__ import annotations

from models.common import PlatformModel


class ExperimentMetrics(PlatformModel):
    """Generic metric container for experiment runs."""

    run_id: str
    experiment_id: str
    values: dict[str, float]
    tags: tuple[str, ...] = ()

    def get(self, name: str, default: float = 0.0) -> float:
        return self.values.get(name, default)
