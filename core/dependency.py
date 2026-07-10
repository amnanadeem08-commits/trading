"""Core entity dependency validation."""

from __future__ import annotations

from dataclasses import dataclass

from core.errors.exceptions import CircularEntityDependencyError


@dataclass(frozen=True)
class DependencyGraph:
    """Directed dependency graph for core entities."""

    nodes: tuple[str, ...]
    edges: dict[str, tuple[str, ...]]


def build_dependency_graph(
    nodes: tuple[str, ...],
    dependencies: dict[str, tuple[str, ...]],
) -> DependencyGraph:
    """Build a dependency graph from node identifiers and dependency maps."""
    return DependencyGraph(nodes=nodes, edges=dependencies)


def detect_cycle(graph: DependencyGraph) -> tuple[str, ...] | None:
    """Detect a cycle in the dependency graph."""
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def visit(node: str) -> tuple[str, ...] | None:
        if node in stack:
            cycle_start = path.index(node)
            return tuple([*path[cycle_start:], node])
        if node in visited:
            return None
        visited.add(node)
        stack.add(node)
        path.append(node)
        for dependency in graph.edges.get(node, ()):
            cycle = visit(dependency)
            if cycle is not None:
                return cycle
        path.pop()
        stack.remove(node)
        return None

    for node in graph.nodes:
        cycle = visit(node)
        if cycle is not None:
            return cycle
    return None


def topological_order(graph: DependencyGraph) -> tuple[str, ...]:
    """Return a topological ordering of graph nodes."""
    incoming: dict[str, int] = {node: 0 for node in graph.nodes}
    for node in graph.nodes:
        for dependency in graph.edges.get(node, ()):
            if dependency in incoming:
                incoming[node] += 1
    ready = [node for node in graph.nodes if incoming[node] == 0]
    ordered: list[str] = []
    while ready:
        node = ready.pop(0)
        ordered.append(node)
        for target in graph.nodes:
            if node in graph.edges.get(target, ()):
                incoming[target] -= 1
                if incoming[target] == 0:
                    ready.append(target)
    if len(ordered) != len(graph.nodes):
        raise CircularEntityDependencyError(tuple(graph.nodes))
    return tuple(ordered)
