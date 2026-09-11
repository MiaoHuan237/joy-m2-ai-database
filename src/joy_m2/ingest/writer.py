"""Task 9C V1.19 candidate writer API scaffold."""

from __future__ import annotations

from joy_m2.config import PipelineConfig

from .writer_models import V119CandidateArtifacts, V119WriteRequest


def build_v119_candidate(
    request: V119WriteRequest,
    config: PipelineConfig,
) -> V119CandidateArtifacts:
    """Build a V1.19 candidate after Phase B supplies the behavior."""

    raise NotImplementedError("Task 9C writer behavior is not implemented")
