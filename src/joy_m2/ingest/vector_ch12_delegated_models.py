"""Explicit chapter delegated carriers, separate from historical human approvals."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from joy_m2.errors import ImportApprovalError
from . import v124_models as manual

CHAPTER_VALUES = dict(manual._CONTRACT_VALUES,
    approval_schema='task14-v124-ch12-delegated-import-v1',
    candidate_manifest_schema='task14-v124-ch12-candidate-manifest-v1',
    candidate_database_schema='task14-v124-ch12-candidate-v1',
    candidate_identity_schema='task14-v124-ch12-candidate-identity-v1')


@dataclass(frozen=True)
class ChapterSourceDecision:
    """Content-bound decision evidence; never sufficient without external grant."""
    payload: bytes

    def __post_init__(self):
        from .vector_ch12_delegation import _json, _canonical, _validate_review
        try:
            if type(self.payload) is not bytes:
                raise ValueError('decision must contain canonical bytes')
            p=_json(self.payload)
            if (type(p) is not dict or set(p)!={'schema_version','actor','grant_sha256','mapping','review'}
                    or p['schema_version']!='vector-ch12-delegated-source-decision-v1'
                    or p['actor']!='codex_under_chapter_delegation'
                    or _canonical(p)!=self.payload
                    or type(p['grant_sha256']) is not str or len(p['grant_sha256'])!=64
                    or any(c not in '0123456789abcdef' for c in p['grant_sha256'])):
                raise ValueError('invalid delegated source decision')
            _validate_review(p['review'],p['mapping'])
        except (TypeError,ValueError,KeyError) as error:
            raise ImportApprovalError('invalid chapter source decision') from error

    @property
    def decision_sha256(self):
        return sha256(self.payload).hexdigest()

    @property
    def mapping_sha256(self):
        return json.loads(self.payload)['review']['mapping_sha256']


@dataclass(frozen=True)
class ChapterImportDecision:
    batch_id: str
    preflight_sha256: str
    target_release_version: str
    parent_candidate_digest: str
    statement: str
    grant_sha256: str
    source_decision_json: str
    canonical_closure_json: str

    def __post_init__(self):
        from .vector_ch12_delegation import _json,_canonical
        manual._require_batch_id(self.batch_id)
        for field in ('preflight_sha256','parent_candidate_digest','grant_sha256'):
            manual._require_sha(getattr(self,field),field)
        if self.target_release_version!='V1.24' or type(self.source_decision_json) is not str:
            raise ImportApprovalError('wrong delegated target/source decision')
        source=ChapterSourceDecision(self.source_decision_json.encode())
        content=_json(source.payload)
        if content['grant_sha256']!=self.grant_sha256 or content['mapping']['batch_id']!=self.batch_id:
            raise ImportApprovalError('source decision does not bind import')
        expected=(f'CHAPTER DELEGATED IMPORT BATCH {self.batch_id} {self.preflight_sha256} '
            f'V1.24 PARENT {self.parent_candidate_digest} GRANT {self.grant_sha256} SOURCE {source.decision_sha256}')
        if type(self.statement) is not str or self.statement!=expected:
            raise ImportApprovalError('exact delegated statement required, not human approval')
        if type(self.canonical_closure_json) is not str:
            raise ImportApprovalError('canonical closure required')
        closure=_json(self.canonical_closure_json)
        if (type(closure) is not dict or 'import_manifest.json' not in closure
                or _canonical(closure).decode()!=self.canonical_closure_json):
            raise ImportApprovalError('invalid canonical closure')
        from .v124_writer_profiles import relative_path
        for name,row in closure.items():
            relative_path(name)
            if type(row) is not dict or set(row)!={'sha256','size_bytes'}:
                raise ImportApprovalError('invalid canonical file evidence')
            manual._require_sha(row['sha256'],'canonical sha256')
            if type(row['size_bytes']) is not int or row['size_bytes']<0:
                raise ImportApprovalError('invalid canonical size')


@dataclass(frozen=True)
class ChapterContract(manual.V124CandidateContract):
    def __post_init__(self):
        for name,value in CHAPTER_VALUES.items():
            if type(getattr(self,name)) is not type(value) or getattr(self,name)!=value:
                raise ImportApprovalError('fixed chapter contract mismatch')
        if (manual._exact_tuple(self.required_candidate_tables,str,'tables')!=manual._CANDIDATE_TABLES
                or manual._exact_tuple(self.required_candidate_views,str,'views')!=manual._CANDIDATE_VIEWS):
            raise ImportApprovalError('chapter candidate objects mismatch')
        object.__setattr__(self,'required_candidate_tables',manual._CANDIDATE_TABLES)
        object.__setattr__(self,'required_candidate_views',manual._CANDIDATE_VIEWS)


def chapter_contract():
    return ChapterContract(**CHAPTER_VALUES,
        required_candidate_tables=manual._CANDIDATE_TABLES,
        required_candidate_views=manual._CANDIDATE_VIEWS)


@dataclass(frozen=True)
class ChapterApprovedBatch:
    preflight_result: object
    package_root: Path
    approval: ChapterImportDecision

    def __post_init__(self):
        raise ImportApprovalError('chapter approved batch not implemented')
