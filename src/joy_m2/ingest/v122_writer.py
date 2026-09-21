"""V1.22 writer API scaffold; behavior not implemented."""
from pathlib import Path
from joy_m2.config import PipelineConfig
from joy_m2.models import VerificationReport
from .v122_models import V122CandidateBuildRequest, V122CandidateArtifacts


def build_v122_candidate(request: V122CandidateBuildRequest, config: PipelineConfig) -> V122CandidateArtifacts:
    raise NotImplementedError("V1.22 writer behavior not implemented")
