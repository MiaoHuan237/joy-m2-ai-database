"""V1.24 publication scaffolds; no authority bypass."""
from joy_m2.config import PipelineConfig
from .v124_promotion_models import V124PromotionBuildRequest, V124PublicationRequest, V124PromotionArtifacts

def build_v124_promotion(request: V124PromotionBuildRequest, config: PipelineConfig) -> V124PromotionArtifacts:
    return None

def publish_v124_release(request: V124PublicationRequest, config: PipelineConfig) -> V124PromotionArtifacts:
    return None
