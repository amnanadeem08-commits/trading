"""Lineage edge contract."""

from __future__ import annotations

from models.common import PlatformModel


class LineageEdge(PlatformModel):
    """Directed edge in the model lineage graph."""

    edge_id: str
    source_id: str
    target_id: str
    relation: str
