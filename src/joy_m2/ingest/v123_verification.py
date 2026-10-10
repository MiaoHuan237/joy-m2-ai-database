"""V1.23 API scaffold; behavior awaits its own RED checkpoint."""
from joy_m2.config import PipelineConfig
from joy_m2.models import VerificationReport
from .v123_models import V123CandidateVerificationRequest


def verify_v123_candidate(request: V123CandidateVerificationRequest, config: PipelineConfig) -> VerificationReport:
    raise NotImplementedError("V1.23 verification not implemented")
