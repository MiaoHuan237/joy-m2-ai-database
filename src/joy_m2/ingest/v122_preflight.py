"""V1.22 preflight API scaffold; behavior not implemented."""
from pathlib import Path
from joy_m2.config import PipelineConfig
from joy_m2.models import VerificationReport
from .v122_models import V122PreflightRequest, V122ImportPreflightResult


def preflight_v122_import(request: V122PreflightRequest, config: PipelineConfig) -> V122ImportPreflightResult:
    raise NotImplementedError("V1.22 preflight behavior not implemented")
