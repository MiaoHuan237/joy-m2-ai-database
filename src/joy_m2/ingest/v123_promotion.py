"""V1.23 promotion callable scaffolds; behavior follows valid RED."""
from joy_m2.config import PipelineConfig
from .v123_promotion_models import V123PromotionBuildRequest, V123PublicationRequest, V123PromotionArtifacts

def build_v123_promotion(request: V123PromotionBuildRequest, config: PipelineConfig) -> V123PromotionArtifacts:
    return None

def publish_v123_release(request: V123PublicationRequest, config: PipelineConfig) -> V123PromotionArtifacts:
    return None
