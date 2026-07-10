"""Inference version contracts."""

from __future__ import annotations

from threading import RLock

from inference_pipeline.exceptions import InferencePipelineError
from models.common import PlatformModel, UTCDateTime, utc_now


class InferenceVersion(PlatformModel):
    """Version record for the inference pipeline."""

    version_id: str
    pipeline_schema: str
    configuration_hash: str = ""
    created_at: UTCDateTime


class InferenceVersionRegistry:
    """Registry for inference pipeline schema versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, InferenceVersion] = {}
        self._latest: str | None = None

    def register(
        self,
        *,
        version_id: str,
        pipeline_schema: str,
        configuration_hash: str = "",
    ) -> InferenceVersion:
        if not version_id.strip():
            msg = "version_id must not be empty"
            raise InferencePipelineError(msg)
        version = InferenceVersion(
            version_id=version_id,
            pipeline_schema=pipeline_schema,
            configuration_hash=configuration_hash,
            created_at=utc_now(),
        )
        with self._lock:
            self._versions[version_id] = version
            self._latest = version_id
        return version

    def get(self, version_id: str) -> InferenceVersion:
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            msg = f"Inference version not found: {version_id}"
            raise InferencePipelineError(msg)
        return version

    def latest(self) -> InferenceVersion | None:
        with self._lock:
            if self._latest is None:
                return None
            return self._versions.get(self._latest)

    def list_versions(self) -> tuple[InferenceVersion, ...]:
        with self._lock:
            return tuple(self._versions[vid] for vid in sorted(self._versions))
