"""V1.21 candidate verification boundary."""

from joy_m2.config import PipelineConfig
from joy_m2.models import VerificationReport

from .v121_models import V121CandidateVerificationRequest


__all__ = ("verify_v121_candidate",)


def verify_v121_candidate(
    request: V121CandidateVerificationRequest,
    config: PipelineConfig,
) -> VerificationReport:
    raise NotImplementedError("V1.21 candidate verification is not implemented")
