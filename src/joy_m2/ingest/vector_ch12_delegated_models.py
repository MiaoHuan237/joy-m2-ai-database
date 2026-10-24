"""Explicit chapter delegated carriers, separate from historical human approvals."""
from dataclasses import dataclass,fields
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
        exact(self.preflight_result,(manual.V124ImportPreflightResult,ChapterPreflightResult))
        exact(self.approval,(ChapterImportDecision,))
        object.__setattr__(self,'package_root',manual._path(self.package_root,'package_root'))
        report=self.preflight_result.report
        if (report.status!='READY FOR USER IMPORT APPROVAL' or report.blocking_errors
                or self.preflight_result.issues or self.approval.batch_id!=report.batch_id
                or self.approval.preflight_sha256!=report.preflight_sha256
                or self.approval.parent_candidate_digest!=report.parent_candidate_digest):
            raise ImportApprovalError('chapter decision does not bind READY batch')


@dataclass(frozen=True)
class ChapterLedgerEntry(manual.V124BatchLedgerEntry):
    approval: ChapterImportDecision
    def __post_init__(self):
        exact(self.approval,(ChapterImportDecision,))
        manual._require_batch_id(self.batch_id)
        for name in ('parent_candidate_digest','preflight_sha256','manifest_sha256'):
            manual._require_sha(getattr(self,name),name)
        if type(self.ordinal) is not int or self.ordinal<1:
            raise ImportApprovalError('invalid ledger ordinal')
        if self.ordinal==1 and self.parent_candidate_digest!=manual._GENESIS_DIGEST:
            raise ImportApprovalError('invalid first parent')
        for name in ('batch_id','parent_candidate_digest','preflight_sha256'):
            if getattr(self,name)!=getattr(self.approval,name):
                raise ImportApprovalError('ledger decision mismatch')
        for name in ('batch_candidate_count','cumulative_candidate_count','projected_question_count'):
            if type(getattr(self,name)) is not int or getattr(self,name)<0:
                raise ImportApprovalError('invalid ledger counts')
        if self.cumulative_candidate_count<self.batch_candidate_count or self.projected_question_count!=677+self.cumulative_candidate_count:
            raise ImportApprovalError('ledger count closure')


@dataclass(frozen=True)
class ChapterEffectiveState(manual.V124EffectiveState):
    batch_ledger: tuple[manual.V124BatchLedgerEntry | ChapterLedgerEntry,...]
    def __post_init__(self):
        manual._baseline_artifact(self.baseline_database,'baseline_database')
        manual._require_sha(self.candidate_digest,'candidate_digest')
        ledger=exact_tuple(self.batch_ledger,(manual.V124BatchLedgerEntry,ChapterLedgerEntry))
        if any(type(x) is not int or x<0 for x in (self.candidate_count,self.projected_question_count)):
            raise ImportApprovalError('invalid effective counts')
        previous=0;ids=set();preflights=set()
        for ordinal,entry in enumerate(ledger,1):
            if (entry.ordinal!=ordinal or entry.batch_id in ids or entry.preflight_sha256 in preflights
                    or entry.cumulative_candidate_count!=previous+entry.batch_candidate_count):
                raise ImportApprovalError('mixed ledger order/identity/count mismatch')
            previous=entry.cumulative_candidate_count;ids.add(entry.batch_id);preflights.add(entry.preflight_sha256)
        if (self.candidate_count!=previous or self.projected_question_count!=677+previous
                or not ledger and self.candidate_digest!=manual._GENESIS_DIGEST):
            raise ImportApprovalError('effective state closure')
        object.__setattr__(self,'batch_ledger',ledger)


@dataclass(frozen=True)
class ChapterPreflightResult(manual.V124ImportPreflightResult):
    effective_state: ChapterEffectiveState
    def __post_init__(self):
        exact(self.manifest,(manual.V124BatchImportManifest,))
        exact(self.effective_state,(ChapterEffectiveState,))
        exact(self.report,(manual.V124ImportPreflightReport,))
        if (self.report.batch_id!=self.manifest.batch_id
                or self.report.parent_candidate_digest!=self.effective_state.candidate_digest
                or self.report.parent_batch_count!=len(self.effective_state.batch_ledger)
                or self.report.before_count!=self.effective_state.projected_question_count):
            raise ImportApprovalError('chapter preflight state mismatch')
        object.__setattr__(self,'candidates',exact_tuple(self.candidates,(manual.ImportCandidate,)))
        issues=exact_tuple(self.issues,(manual.ImportIssue,))
        object.__setattr__(self,'issues',tuple(sorted(issues,key=lambda i:(i.proposed_question_id or '',i.code,i.field,i.evidence))))


@dataclass(frozen=True)
class ChapterBuildRequest:
    approved_batches: tuple[manual.V124ApprovedBatch | ChapterApprovedBatch,...]
    output_dir: Path
    contract: ChapterContract
    def __post_init__(self):
        validate_request(self,'output_dir')


@dataclass(frozen=True)
class ChapterVerificationRequest:
    candidate_dir: Path
    approved_batches: tuple[manual.V124ApprovedBatch | ChapterApprovedBatch,...]
    contract: ChapterContract
    def __post_init__(self):
        validate_request(self,'candidate_dir')


@dataclass(frozen=True)
class ChapterPreflightRequest:
    manifest: manual.V124BatchImportManifest
    package_root: Path
    baseline_database: manual.ArtifactRef
    parent_candidate: manual.V124CandidateVerificationRequest | ChapterVerificationRequest
    contract: ChapterContract
    def __post_init__(self):
        exact(self.manifest,(manual.V124BatchImportManifest,))
        manual._baseline_artifact(self.baseline_database,'baseline_database')
        exact(self.contract,(ChapterContract,))
        if self.parent_candidate is not None:
            exact(self.parent_candidate,(manual.V124CandidateVerificationRequest,ChapterVerificationRequest))
        object.__setattr__(self,'package_root',manual._path(self.package_root,'package_root'))


@dataclass(frozen=True)
class ChapterArtifacts(manual.V124CandidateArtifacts):
    state: ChapterEffectiveState
    def __post_init__(self):
        for name,kind in (('database','sqlite'),('manifest','manifest'),('sha256sums','sha256sums'),('rollback','rollback')):
            manual._artifact(getattr(self,name),name,kind)
        for name,kinds in (('batch_authorities',('preflight','approval')),('images',('image',))):
            refs=exact_tuple(getattr(self,name),(manual.ArtifactRef,))
            if any(r.kind not in kinds for r in refs) or refs!=tuple(sorted(refs,key=lambda r:r.path.as_posix())):
                raise ImportApprovalError('artifact kind/order mismatch')
            object.__setattr__(self,name,refs)
        exact(self.state,(ChapterEffectiveState,))
        exact(self.verification_report,(manual.VerificationReport,))


def exact(value,allowed):
    if type(value) not in allowed:
        raise ImportApprovalError('unexpected chapter authority carrier')
    reconstructed=type(value)(**{f.name:getattr(value,f.name) for f in fields(value) if f.init})
    if reconstructed!=value:
        raise ImportApprovalError('forged chapter authority carrier')
    return value


def exact_tuple(values,allowed):
    if type(values) not in (tuple,list):
        raise ImportApprovalError('authority tuple required')
    return tuple(exact(v,allowed) for v in values)


def validate_request(request,path_name):
    batches=exact_tuple(request.approved_batches,(manual.V124ApprovedBatch,ChapterApprovedBatch))
    if not batches or not any(type(b) is ChapterApprovedBatch for b in batches):
        raise ImportApprovalError('chapter request must include delegated batches')
    exact(request.contract,(ChapterContract,))
    object.__setattr__(request,'approved_batches',batches)
    object.__setattr__(request,path_name,manual._lexical_path(getattr(request,path_name),path_name))


def carrier_type(value, manual_type, chapter_type):
    """Closed dispatch only; arbitrary subclasses never acquire authority."""
    return chapter_type if type(value) is chapter_type else manual_type


def nested_valid(batch):
    try:
        exact(batch,(ChapterApprovedBatch,))
        r=batch.preflight_result
        for group in (r.manifest.candidate_records,r.manifest.source_files,r.manifest.answer_files,
                      r.manifest.image_files,r.manifest.teacher_notes_files,r.manifest.common_errors_files):
            exact_tuple(group,(manual.ImportFileEvidence,))
        exact_tuple(r.candidates,(manual.ImportCandidate,));exact_tuple(r.issues,(manual.ImportIssue,))
        exact_tuple(r.report.adaptations,(manual.ImportAdaptation,))
        exact(r.report,(manual.V124ImportPreflightReport,))
        exact(r.effective_state,(manual.V124EffectiveState,ChapterEffectiveState))
        for entry in r.effective_state.batch_ledger:
            exact(entry,(manual.V124BatchLedgerEntry,ChapterLedgerEntry))
            exact(entry.approval,(manual.V124ImportApproval,ChapterImportDecision))
        return True
    except (AttributeError,TypeError,ValueError,manual.PipelineError):
        return False


def uses_delegation(batches):
    return any(type(b) is ChapterApprovedBatch for b in batches)
