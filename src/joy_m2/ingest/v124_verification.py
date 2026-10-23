from joy_m2.config import PipelineConfig
from joy_m2.models import VerificationReport
from .v124_models import V124CandidateVerificationRequest

def verify_v124_candidate(request: V124CandidateVerificationRequest, config: PipelineConfig) -> VerificationReport:
    raise NotImplementedError('V124 verifier pending')
