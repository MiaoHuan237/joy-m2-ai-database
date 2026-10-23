from pathlib import Path
from joy_m2.config import PipelineConfig
from .v124_models import V124PreflightRequest, V124ImportPreflightResult

def preflight_v124_import(request: V124PreflightRequest, config: PipelineConfig) -> V124ImportPreflightResult:
    raise NotImplementedError('V124 preflight pending')

def _formal_indexes(path: Path) -> tuple[dict[str, object], frozenset[str], frozenset[str]]:
    raise NotImplementedError('V124 formal reader pending')
