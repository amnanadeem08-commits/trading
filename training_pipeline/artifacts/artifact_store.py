"""Artifact store for training outputs."""

from __future__ import annotations

import hashlib
import json
from threading import RLock
from uuid import uuid4

from models.common import utc_now
from training_pipeline.artifacts.artifact_metadata import ArtifactManifest, ArtifactMetadata
from training_pipeline.artifacts.model_artifact import ModelArtifact
from training_pipeline.datasets.dataset_reference import DatasetReference
from training_pipeline.exceptions import ArtifactNotFoundError, TrainingJobError


class ArtifactStore:
    """In-memory artifact store for training pipeline outputs."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._artifacts: dict[str, ModelArtifact] = {}

    def store(
        self,
        *,
        experiment_id: str,
        run_id: str,
        job_id: str,
        model_family: str,
        training_version: str,
        dataset: DatasetReference,
        hyperparameters: dict[str, object],
        lineage: tuple[str, ...] | None = None,
    ) -> ModelArtifact:
        artifact_id = f"artifact-{uuid4()}"
        manifest_payload = {
            "artifact_id": artifact_id,
            "experiment_id": experiment_id,
            "run_id": run_id,
            "job_id": job_id,
            "model_family": model_family,
            "training_version": training_version,
            "dataset": dataset.model_dump(mode="json"),
            "hyperparameters": hyperparameters,
        }
        checksum = hashlib.sha256(
            json.dumps(manifest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        metadata = ArtifactMetadata(
            artifact_id=artifact_id,
            experiment_id=experiment_id,
            run_id=run_id,
            job_id=job_id,
            model_family=model_family,
            training_version=training_version,
            dataset=dataset,
            checksum=checksum,
            size_bytes=len(json.dumps(manifest_payload)),
            tags=("orchestration",),
            created_at=utc_now(),
        )
        manifest = ArtifactManifest(
            artifact_id=artifact_id,
            hyperparameters=hyperparameters,
            lineage=lineage or (experiment_id, run_id, dataset.dataset_id),
            reproducibility_key=checksum,
            files=(f"{artifact_id}/manifest.json",),
        )
        artifact = ModelArtifact(
            metadata=metadata,
            manifest=manifest,
            storage_uri=f"memory://artifacts/{artifact_id}",
        )
        with self._lock:
            self._artifacts[artifact_id] = artifact
        return artifact

    def get(self, artifact_id: str) -> ModelArtifact:
        with self._lock:
            artifact = self._artifacts.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)
        return artifact

    def exists(self, artifact_id: str) -> bool:
        with self._lock:
            return artifact_id in self._artifacts

    def list_artifacts(self) -> tuple[ModelArtifact, ...]:
        with self._lock:
            return tuple(self._artifacts[artifact_id] for artifact_id in sorted(self._artifacts))

    def remove(self, artifact_id: str) -> None:
        with self._lock:
            if artifact_id not in self._artifacts:
                raise ArtifactNotFoundError(artifact_id)
            del self._artifacts[artifact_id]

    def validate_manifest(self, artifact: ModelArtifact) -> None:
        if not artifact.manifest.artifact_id:
            msg = "Artifact manifest must include artifact_id"
            raise TrainingJobError(msg)
