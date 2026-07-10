"""Unit tests for lineage graph."""

from __future__ import annotations

import pytest

from model_registry import LineageError, LineageGraph, LineageNodeType
from tests.model_registry_helpers import seed_trained_model


@pytest.mark.unit
def test_lineage_graph_nodes_and_edges() -> None:
    graph = LineageGraph()
    graph.add_node(
        node_id="dataset:ds-1",
        node_type=LineageNodeType.DATASET,
        label="ds-1",
        reference_id="ds-1",
    )
    graph.add_node(
        node_id="job:job-1",
        node_type=LineageNodeType.TRAINING_JOB,
        label="job-1",
        reference_id="job-1",
    )
    graph.add_edge(source_id="dataset:ds-1", target_id="job:job-1", relation="trained_on")
    assert len(graph.nodes()) == 2
    assert len(graph.edges()) == 1


@pytest.mark.unit
def test_lineage_descendants() -> None:
    runtime = seed_trained_model()
    descendants = runtime.lineage.descendants("dataset:dataset-1")
    assert len(descendants) >= 1


@pytest.mark.unit
def test_lineage_unknown_node_raises() -> None:
    graph = LineageGraph()
    with pytest.raises(LineageError):
        graph.get_node("missing")
