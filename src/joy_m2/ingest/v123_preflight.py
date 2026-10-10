"""V1.23 API scaffold; behavior awaits its own RED checkpoint."""
from joy_m2.config import PipelineConfig
from .v123_models import V123PreflightRequest, V123ImportPreflightResult


def preflight_v123_import(request: V123PreflightRequest, config: PipelineConfig) -> V123ImportPreflightResult:
    raise NotImplementedError("V1.23 preflight not implemented")
