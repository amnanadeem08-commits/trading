"""Plugin dependency graph utilities."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field

from models.common import PlatformModel


class PluginDependency(PlatformModel):
    """Dependency on another plugin."""

    plugin_id: str = Field(min_length=1)
    version_minimum: str = Field(min_length=1)
    version_maximum: str | None = None


@dataclass(frozen=True)
class DependencyGraph:
    """Directed dependency graph for plugins."""

    nodes: tuple[str, ...]
    edges: dict[str, tuple[str, ...]]


def build_dependency_graph(
    plugin_ids: tuple[str, ...],
    dependencies: dict[str, tuple[str, ...]],
) -> DependencyGraph:
    """Build a dependency graph from plugin identifiers and edges."""
    edges: dict[str, tuple[str, ...]] = {}
    for plugin_id in plugin_ids:
        known = tuple(dep for dep in dependencies.get(plugin_id, ()) if dep in plugin_ids)
        edges[plugin_id] = known
    return DependencyGraph(nodes=plugin_ids, edges=edges)


def detect_cycle(graph: DependencyGraph) -> tuple[str, ...] | None:
    """Detect a dependency cycle. Returns the cycle path when found."""
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

    for node in sorted(graph.nodes):
        cycle = visit(node)
        if cycle is not None:
            return cycle
    return None


def topological_order(graph: DependencyGraph) -> tuple[str, ...]:
    """Return a topological load order for plugin dependencies."""
    incoming: dict[str, int] = {name: len(graph.edges.get(name, ())) for name in graph.nodes}
    dependents: dict[str, list[str]] = {name: [] for name in graph.nodes}
    for name, deps in graph.edges.items():
        for dependency in deps:
            dependents[dependency].append(name)

    queue = [name for name, count in sorted(incoming.items()) if count == 0]
    order: list[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for dependent in sorted(dependents[current]):
            incoming[dependent] -= 1
            if incoming[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(graph.nodes):
        msg = "Failed to compute plugin load order"
        raise ValueError(msg)
    return tuple(order)
