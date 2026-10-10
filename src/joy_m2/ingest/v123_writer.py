"""V1.23 API scaffold; behavior awaits its own RED checkpoint."""
from joy_m2.config import PipelineConfig
from .v123_models import V123CandidateBuildRequest, V123CandidateArtifacts


def build_v123_candidate(request: V123CandidateBuildRequest, config: PipelineConfig) -> V123CandidateArtifacts:
    raise NotImplementedError("V1.23 writer not implemented")
