"""V1.21 formal promotion entry points."""

from __future__ import annotations

from joy_m2.config import PipelineConfig

from .v121_promotion_models import (
    V121PromotionArtifacts,
    V121PromotionBuildRequest,
    V121PublicationRequest,
)


def build_v121_promotion(
    request: V121PromotionBuildRequest,
    config: PipelineConfig,
) -> V121PromotionArtifacts:
    raise NotImplementedError("V1.21 promotion behavior is not implemented")


def publish_v121_release(
    request: V121PublicationRequest,
    config: PipelineConfig,
) -> V121PromotionArtifacts:
    raise NotImplementedError("V1.21 publication behavior is not implemented")
