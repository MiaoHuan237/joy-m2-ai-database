"""V1.22 verification API scaffold; behavior not implemented."""
from pathlib import Path
from joy_m2.config import PipelineConfig
from joy_m2.models import VerificationReport
from .v122_models import V122CandidateVerificationRequest


def verify_v122_candidate(request: V122CandidateVerificationRequest, config: PipelineConfig) -> VerificationReport:
    raise NotImplementedError("V1.22 verification behavior not implemented")
