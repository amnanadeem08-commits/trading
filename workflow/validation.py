"""Workflow job graph validation."""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.registry import PipelineRegistry
from workflow.exceptions import CircularJobDependencyError, WorkflowValidationError
from workflow.job import Job
from workflow.state import JobState
from workflow.workflow import Workflow


@dataclass(frozen=True)
class WorkflowValidationResult:
    """Outcome of workflow validation."""

    valid: bool
    errors: tuple[str, ...] = ()
    execution_order: tuple[str, ...] = ()


def _jobs_by_id(workflow: Workflow) -> dict[str, Job]:
    return {job.job_id: job for job in workflow.jobs}


def _build_dependency_graph(jobs: dict[str, Job]) -> dict[str, tuple[str, ...]]:
    graph: dict[str, tuple[str, ...]] = {}
    for job_id, job in jobs.items():
        dependencies = tuple(dep for dep in job.dependencies if dep in jobs)
        graph[job_id] = dependencies
    return graph


def _detect_cycle(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...] | None:
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
        for dependency in graph.get(node, ()):
            cycle = visit(dependency)
            if cycle is not None:
                return cycle
        path.pop()
        stack.remove(node)
        return None

    for node in sorted(graph):
        cycle = visit(node)
        if cycle is not None:
            return cycle
    return None


def _topological_order(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    incoming: dict[str, int] = {name: len(deps) for name, deps in graph.items()}
    dependents: dict[str, list[str]] = {name: [] for name in graph}
    for name, dependencies in graph.items():
        for dependency in dependencies:
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

    if len(order) != len(graph):
        msg = "Failed to compute job execution order"
        raise WorkflowValidationError(msg)
    return tuple(order)


def validate_workflow(
    workflow: Workflow,
    pipeline_registry: PipelineRegistry,
    *,
    job_states: dict[str, JobState] | None = None,
) -> WorkflowValidationResult:
    """Validate workflow jobs, pipelines, and dependency ordering."""
    errors: list[str] = []
    jobs = _jobs_by_id(workflow)
    job_ids = [job.job_id for job in workflow.jobs]
    if len(job_ids) != len(set(job_ids)):
        errors.append("Duplicate job identifiers detected")

    for job in workflow.jobs:
        if job.job_id not in jobs:
            continue
        for dependency in job.dependencies:
            if dependency == job.job_id:
                errors.append(f"Job depends on itself: {job.job_id}")
            elif dependency not in jobs:
                errors.append(f"Missing dependency '{dependency}' required by '{job.job_id}'")
        if not pipeline_registry.exists(job.pipeline_name):
            errors.append(f"Pipeline not registered for job '{job.job_id}': {job.pipeline_name}")

    if job_states is not None:
        for job_id in job_states:
            if job_id not in jobs:
                errors.append(f"Unknown job state target: {job_id}")

    if errors:
        return WorkflowValidationResult(valid=False, errors=tuple(errors))

    graph = _build_dependency_graph(jobs)
    cycle = _detect_cycle(graph)
    if cycle is not None:
        raise CircularJobDependencyError(cycle)

    return WorkflowValidationResult(
        valid=True,
        execution_order=_topological_order(graph),
    )
