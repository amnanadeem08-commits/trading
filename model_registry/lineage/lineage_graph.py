"""In-memory lineage graph."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from model_registry.exceptions import LineageError
from model_registry.lineage.lineage_edge import LineageEdge
from model_registry.lineage.lineage_node import LineageNode, LineageNodeType


class LineageGraph:
    """Tracks relationships between datasets, jobs, experiments, artifacts, and models."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._nodes: dict[str, LineageNode] = {}
        self._edges: dict[str, LineageEdge] = {}
        self._outgoing: dict[str, tuple[str, ...]] = {}

    def add_node(
        self,
        *,
        node_id: str,
        node_type: LineageNodeType,
        label: str,
        reference_id: str,
    ) -> LineageNode:
        node = LineageNode(
            node_id=node_id,
            node_type=node_type,
            label=label,
            reference_id=reference_id,
        )
        with self._lock:
            self._nodes[node_id] = node
            self._outgoing.setdefault(node_id, ())
        return node

    def add_edge(self, *, source_id: str, target_id: str, relation: str) -> LineageEdge:
        with self._lock:
            if source_id not in self._nodes or target_id not in self._nodes:
                msg = f"Cannot link unknown nodes: {source_id} -> {target_id}"
                raise LineageError(msg)
            edge_id = f"edge-{uuid4()}"
            edge = LineageEdge(
                edge_id=edge_id,
                source_id=source_id,
                target_id=target_id,
                relation=relation,
            )
            self._edges[edge_id] = edge
            outgoing = self._outgoing.get(source_id, ())
            self._outgoing[source_id] = (*outgoing, edge_id)
        return edge

    def get_node(self, node_id: str) -> LineageNode:
        with self._lock:
            node = self._nodes.get(node_id)
        if node is None:
            msg = f"Lineage node not found: {node_id}"
            raise LineageError(msg)
        return node

    def nodes(self) -> tuple[LineageNode, ...]:
        with self._lock:
            return tuple(self._nodes[node_id] for node_id in sorted(self._nodes))

    def edges(self) -> tuple[LineageEdge, ...]:
        with self._lock:
            return tuple(self._edges[edge_id] for edge_id in sorted(self._edges))

    def descendants(self, node_id: str) -> tuple[LineageNode, ...]:
        with self._lock:
            if node_id not in self._nodes:
                msg = f"Lineage node not found: {node_id}"
                raise LineageError(msg)
            visited: set[str] = set()
            queue = [node_id]
            collected: list[LineageNode] = []
            while queue:
                current = queue.pop(0)
                for edge_id in self._outgoing.get(current, ()):
                    edge = self._edges[edge_id]
                    if edge.target_id in visited:
                        continue
                    visited.add(edge.target_id)
                    target = self._nodes[edge.target_id]
                    collected.append(target)
                    queue.append(edge.target_id)
        return tuple(collected)

    def record_training_lineage(
        self,
        *,
        dataset_id: str,
        job_id: str,
        experiment_id: str,
        artifact_id: str,
        model_id: str,
        version_id: str,
    ) -> None:
        self.add_node(
            node_id=f"dataset:{dataset_id}",
            node_type=LineageNodeType.DATASET,
            label=dataset_id,
            reference_id=dataset_id,
        )
        self.add_node(
            node_id=f"job:{job_id}",
            node_type=LineageNodeType.TRAINING_JOB,
            label=job_id,
            reference_id=job_id,
        )
        self.add_node(
            node_id=f"experiment:{experiment_id}",
            node_type=LineageNodeType.EXPERIMENT,
            label=experiment_id,
            reference_id=experiment_id,
        )
        self.add_node(
            node_id=f"artifact:{artifact_id}",
            node_type=LineageNodeType.ARTIFACT,
            label=artifact_id,
            reference_id=artifact_id,
        )
        self.add_node(
            node_id=f"model:{model_id}",
            node_type=LineageNodeType.REGISTERED_MODEL,
            label=model_id,
            reference_id=model_id,
        )
        self.add_node(
            node_id=f"version:{version_id}",
            node_type=LineageNodeType.MODEL_VERSION,
            label=version_id,
            reference_id=version_id,
        )
        self.add_edge(
            source_id=f"dataset:{dataset_id}",
            target_id=f"job:{job_id}",
            relation="trained_on",
        )
        self.add_edge(
            source_id=f"job:{job_id}",
            target_id=f"experiment:{experiment_id}",
            relation="executed",
        )
        self.add_edge(
            source_id=f"experiment:{experiment_id}",
            target_id=f"artifact:{artifact_id}",
            relation="produced",
        )
        self.add_edge(
            source_id=f"artifact:{artifact_id}",
            target_id=f"model:{model_id}",
            relation="registered_as",
        )
        self.add_edge(
            source_id=f"model:{model_id}",
            target_id=f"version:{version_id}",
            relation="versioned",
        )
