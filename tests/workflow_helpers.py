"""Helpers for workflow tests."""

from __future__ import annotations

from pipeline import PipelineBuilder, PipelineRegistry
from tests.pipeline_fixtures import IngestStage, TransformStage
from workflow import Job, Workflow, WorkflowRegistry


def setup_ingest_pipeline(registry: PipelineRegistry) -> None:
    pipeline = PipelineBuilder("ingest-pipeline").add_stage(IngestStage()).build()
    registry.register_pipeline(pipeline)


def setup_transform_pipeline(registry: PipelineRegistry) -> None:
    pipeline = (
        PipelineBuilder("transform-pipeline")
        .add_stage(IngestStage())
        .add_stage(TransformStage())
        .build()
    )
    registry.register_pipeline(pipeline)


def make_single_job_workflow(*, workflow_id: str = "wf-single") -> Workflow:
    return Workflow(
        workflow_id=workflow_id,
        version="1.0.0",
        jobs=(
            Job(
                job_id="job-ingest",
                pipeline_name="ingest-pipeline",
            ),
        ),
    )


def make_dependent_workflow(*, workflow_id: str = "wf-chain") -> Workflow:
    return Workflow(
        workflow_id=workflow_id,
        version="1.0.0",
        jobs=(
            Job(job_id="job-ingest", pipeline_name="ingest-pipeline"),
            Job(
                job_id="job-transform",
                pipeline_name="transform-pipeline",
                dependencies=("job-ingest",),
            ),
        ),
    )


def register_workflow(registry: WorkflowRegistry, workflow: Workflow) -> None:
    registry.register(workflow)
