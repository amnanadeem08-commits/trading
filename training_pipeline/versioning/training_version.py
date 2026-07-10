"""Training version contracts."""

from __future__ import annotations

from threading import RLock

from models.common import PlatformModel, UTCDateTime, utc_now
from training_pipeline.exceptions import TrainingJobError


class TrainingVersion(PlatformModel):
    """Version record for a training job or experiment."""

    version_id: str
    job_id: str
    experiment_id: str
    semantic_version: str
    configuration_hash: str = ""
    created_at: UTCDateTime


class TrainingVersionRegistry:
    """Registry for training version records."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, TrainingVersion] = {}
        self._by_job: dict[str, tuple[str, ...]] = {}

    def register(
        self,
        *,
        version_id: str,
        job_id: str,
        experiment_id: str,
        semantic_version: str,
        configuration_hash: str = "",
    ) -> TrainingVersion:
        if not version_id.strip():
            msg = "version_id must not be empty"
            raise TrainingJobError(msg)
        version = TrainingVersion(
            version_id=version_id,
            job_id=job_id,
            experiment_id=experiment_id,
            semantic_version=semantic_version,
            configuration_hash=configuration_hash,
            created_at=utc_now(),
        )
        with self._lock:
            self._versions[version_id] = version
            job_versions = self._by_job.get(job_id, ())
            if version_id not in job_versions:
                self._by_job[job_id] = (*job_versions, version_id)
        return version

    def get(self, version_id: str) -> TrainingVersion:
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            msg = f"Training version not found: {version_id}"
            raise TrainingJobError(msg)
        return version

    def list_for_job(self, job_id: str) -> tuple[TrainingVersion, ...]:
        with self._lock:
            version_ids = self._by_job.get(job_id, ())
            return tuple(self._versions[vid] for vid in version_ids if vid in self._versions)

    def latest_for_job(self, job_id: str) -> TrainingVersion | None:
        versions = self.list_for_job(job_id)
        if not versions:
            return None
        return versions[-1]
