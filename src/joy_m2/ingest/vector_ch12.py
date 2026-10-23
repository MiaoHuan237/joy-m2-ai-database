"""Explicit chapter 12 dual-package source profile; no real writer."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import TYPE_CHECKING

from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError
from joy_m2.ingest.source_mapping import SourceMappingApproval

if TYPE_CHECKING:
    from joy_m2.ingest.v124_models import V124AdaptedImportPackage


@dataclass(frozen=True)
class VectorCh12Proposal:
    proposal_root: Path
    mapping_path: Path
    review_path: Path
    source_id: str
    input_binding_sha256: str
    mapping_sha256: str
    candidate_count: int

    def __post_init__(self):
        for name in ('proposal_root', 'mapping_path', 'review_path'):
            if not isinstance(getattr(self, name), Path):
                raise PipelineError(f'{name} must be a Path')
        if self.mapping_path != self.proposal_root/'source_mapping.json':
            raise PipelineError('mapping_path must be inside proposal_root')
        if self.review_path != self.proposal_root/'SOURCE_MAPPING_REVIEW.md':
            raise PipelineError('review_path must be inside proposal_root')
        if type(self.source_id) is not str or not self.source_id:
            raise PipelineError('source_id must be nonempty')
        for name in ('input_binding_sha256', 'mapping_sha256'):
            value = getattr(self, name)
            if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
                raise PipelineError(f'{name} must be SHA256')
        if type(self.candidate_count) is not int or self.candidate_count < 0:
            raise PipelineError('candidate_count must be nonnegative integer')


def propose_vector_ch12_mapping(textbook_path: Path, answers_path: Path,
                               draft_path: Path, proposal_dir: Path,
                               config: PipelineConfig) -> VectorCh12Proposal:
    raise NotImplementedError("chapter12 proposal not implemented")


def adapt_vector_ch12_from_mapping(textbook_path: Path, answers_path: Path,
                                  mapping_path: Path, approval: SourceMappingApproval,
                                  output_dir: Path, config: PipelineConfig
                                  ) -> V124AdaptedImportPackage:
    raise NotImplementedError("chapter12 canonical bridge not implemented")
