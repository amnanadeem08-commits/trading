"""Lineage node contract."""

from __future__ import annotations

from enum import StrEnum

from models.common import PlatformModel


class LineageNodeType(StrEnum):
    """Type of entity represented in the lineage graph."""

    DATASET = "dataset"
    TRAINING_JOB = "training_job"
    EXPERIMENT = "experiment"
    ARTIFACT = "artifact"
    REGISTERED_MODEL = "registered_model"
    MODEL_VERSION = "model_version"


class LineageNode(PlatformModel):
    """Node in the model lineage graph."""

    node_id: str
    node_type: LineageNodeType
    label: str
    reference_id: str
