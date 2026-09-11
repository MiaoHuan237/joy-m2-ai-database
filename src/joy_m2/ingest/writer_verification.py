"""Task 9C V1.19 candidate verifier API scaffold."""

from __future__ import annotations

from joy_m2.config import PipelineConfig
from joy_m2.models import VerificationReport

from .writer_models import V119VerificationRequest


def verify_v119_candidate(
    request: V119VerificationRequest,
    config: PipelineConfig,
) -> VerificationReport:
    """Verify a V1.19 candidate after Phase B supplies the behavior."""

    raise NotImplementedError("Task 9C writer behavior is not implemented")
