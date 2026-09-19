"""Independent V1.21 formal promotion verification entry point."""

from __future__ import annotations

from joy_m2.config import PipelineConfig
from joy_m2.models import VerificationReport

from .v121_promotion_models import V121PromotionVerificationRequest


def verify_v121_promotion(
    request: V121PromotionVerificationRequest,
    config: PipelineConfig,
) -> VerificationReport:
    raise NotImplementedError("V1.21 promotion verification is not implemented")
