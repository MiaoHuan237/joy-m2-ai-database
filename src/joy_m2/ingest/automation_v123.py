"""Fixed V1.23 operational backend; existing contracts remain authoritative."""
from dataclasses import asdict
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from joy_m2.config import PipelineConfig
from joy_m2.models import ArtifactRef
from .automation import canonical, read_json, save_json, safe_runtime, sha, fingerprint
from .v123_models import (
    V123CandidateContract, V123PreflightRequest, V123ImportApproval,
    V123ApprovedBatch, V123CandidateBuildRequest, V123CandidateVerificationRequest,
    _CONTRACT_VALUES, _CANDIDATE_TABLES, _CANDIDATE_VIEWS,
)
from .v123_manifest import load_v123_import_manifest
from .v123_preflight import preflight_v123_import, _formal_indexes
from .v123_writer import build_v123_candidate
from .v123_verification import verify_v123_candidate


def plain(value):
    return __import__('json').loads(__import__('json').dumps(asdict(value), default=str))


def load_proposal(root):
    from .hkdse_pdf_models import (
        HkdsePdfPageSpan, HkdsePdfTranscriptionRecord, HkdsePdfTranscriptionIssue,
        HkdsePdfTranscriptionBatch,
    )
    data = read_json(root/'transcription.json')
    digest = data.pop('transcription_digest')
    if hashlib.sha256(canonical(data).encode()).hexdigest() != digest:
        raise ValueError('proposal digest mismatch')
    records = []
    for row in data['records']:
        row = dict(row)
        for key in ('question_pages', 'ms_pages'):
            row[key] = HkdsePdfPageSpan(**row[key])
        records.append(HkdsePdfTranscriptionRecord(**row))
    issues = [HkdsePdfTranscriptionIssue(**{**row, 'evidence': canonical(row['evidence'])}) for row in data['issues']]
    return HkdsePdfTranscriptionBatch(data['batch_id'], data['staging_sha256'], data['pp_sha256'],
                                    data['ms_sha256'], tuple(records), tuple(issues), digest, root,
                                    root/'transcription.json', root/'PDF_TRANSCRIPTION_REVIEW.md')

class V123Operations:
    def __init__(self, repo_root, runtime_root, receipts):
        self.config = PipelineConfig(repo_root)
        self.runtime = runtime_root
        discovered = {p.resolve() for p in self.config.staging_root.glob('task13-v123*/**/REAL_BATCH_IMPORT_RECEIPT.json')}
        if not discovered.issubset({Path(p).resolve() for p in receipts}):
            raise ValueError('unconfigured operational receipt; reconcile current parent before continuing')
        self.contract = V123CandidateContract(**_CONTRACT_VALUES,
            required_candidate_tables=_CANDIDATE_TABLES, required_candidate_views=_CANDIDATE_VIEWS)
        path = self.config.releases_root/'V1.22/Joy_M2_Complete_Question_DB_V1_22.sqlite3'
        self.baseline = ArtifactRef(path, sha(path), path.stat().st_size, 'sqlite')
        self.batches = []
        self.parent = None
        self.accepted = {}
        own = sorted((runtime_root/'receipts').glob('*.json'))
        paths = [Path(p) for p in receipts] + own
        for receipt_path in paths:
            receipt = read_json(receipt_path)
            batch_id = receipt['approval']['batch_id']
            if batch_id in self.accepted:
                raise ValueError('duplicate receipt in prefix: ' + batch_id)
            package = Path(receipt['package_root'])
            result = self.preflight(package)
            approved = V123ApprovedBatch(result, package, V123ImportApproval(**receipt['approval']))
            self.batches.append(approved)
            request = V123CandidateVerificationRequest(Path(receipt['candidate_dir']), tuple(self.batches), self.contract)
            verification = verify_v123_candidate(request, self.config)
            if verification.status != 'PASS':
                raise ValueError('prefix verifier failed: ' + batch_id)
            actual = read_json(request.candidate_dir/self.contract.manifest_filename)
            if actual['candidate_digest'] != receipt['candidate_digest']:
                raise ValueError('receipt candidate identity mismatch')
            self.parent = request
            self.accepted[batch_id] = {**receipt, 'receipt_path': str(receipt_path)}
        pending = runtime_root/'pending-write.json'
        if pending.exists():
            intent = read_json(pending)
            approval = V123ImportApproval(**intent['approval'])
            if approval.batch_id in self.accepted:
                receipt = self.accepted[approval.batch_id]
                if receipt['approval'] != intent['approval'] or receipt['package_root'] != intent['package_root']:
                    raise ValueError('pending intent conflicts with verified receipt')
                pending.unlink()
            else:
                package = Path(intent['package_root'])
                result = self.preflight(package)
                self.finish_write(package, result, approval, intent['revision'])

    def preflight(self, package):
        return preflight_v123_import(V123PreflightRequest(
            load_v123_import_manifest(package/'import_manifest.json'), package,
            self.baseline, self.parent, self.contract), self.config)

    def transcription(self, job):
        from .hkdse_pdf_adapter import (
            propose_hkdse_pdf_transcription, approve_hkdse_pdf_transcription,
            adapt_verified_hkdse_pdf_transcription_v123,
        )
        from .hkdse_pdf_models import HkdsePdfTranscriptionApproval
        inputs = {k: Path(v) for k, v in job['inputs'].items()}
        identity = hashlib.sha256(canonical({k:fingerprint(p) for k,p in inputs.items()}).encode()).hexdigest()
        output = safe_runtime(self.runtime/'proposals'/identity, self.config.repo_root)
        if not output.exists():
            propose_hkdse_pdf_transcription(inputs['staging'], inputs['pp'], inputs['ms'],
                                           inputs['pass_a'], inputs['pass_b'], output, self.config)
        proposal = load_proposal(output)
        # Re-consolidate existing evidence passes, not OCR/model extraction.
        # A self-consistent cached digest alone cannot bind the actual inputs.
        with TemporaryDirectory(dir=self.runtime) as temporary:
            expected = propose_hkdse_pdf_transcription(inputs['staging'], inputs['pp'], inputs['ms'],
                inputs['pass_a'], inputs['pass_b'], Path(temporary)/'proposal', self.config)
            if expected.transcription_digest != proposal.transcription_digest:
                raise ValueError('cached proposal differs from current source/pass payload')
        if proposal.batch_id != job['source_id']:
            raise ValueError('source ID does not match proposal')
        if proposal.issues:
            return None, {'status': 'REVIEW_REQUIRED', 'issues': [plain(x) for x in proposal.issues],
                          'proposal_path': str(proposal.transcription_path)}
        _, primary_types, tags = _formal_indexes(self.baseline.path)
        taxonomy = [{'id':r.staging_id, 'unknown_primary_type':r.module_proposal not in primary_types,
                     'unknown_tags':sorted(set(r.tag_proposals)-tags)} for r in proposal.records
                    if r.module_proposal not in primary_types or set(r.tag_proposals)-tags]
        if taxonomy:
            return None, {'status':'REVIEW_REQUIRED', 'taxonomy_issues':taxonomy,
                          'proposal_path':str(proposal.transcription_path)}
        statement = f'USER APPROVED PDF TRANSCRIPTION BATCH {proposal.batch_id} {proposal.transcription_digest}'
        approval_path = Path(job.get('transcription_approval', self.runtime/'absent-approval'))
        actual = approval_path.read_text().strip() if approval_path.is_file() else None
        if actual != statement:
            return None, {'status': 'AWAITING_TRANSCRIPTION_APPROVAL', 'required_approval': statement,
                          'transcription_digest': proposal.transcription_digest, 'proposal_path': str(proposal.transcription_path)}
        verified = approve_hkdse_pdf_transcription(proposal, HkdsePdfTranscriptionApproval(proposal.batch_id, proposal.transcription_digest, actual))
        package = safe_runtime(self.runtime/'packages'/identity, self.config.repo_root)
        if not package.exists():
            adapt_verified_hkdse_pdf_transcription_v123(verified, package, self.config)
        else:
            with TemporaryDirectory(dir=self.runtime) as temporary:
                expected = Path(temporary)/'package'
                adapt_verified_hkdse_pdf_transcription_v123(verified, expected, self.config)
                def files(root):
                    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
                if any(p.is_symlink() for p in package.rglob('*')) or files(package) != files(expected):
                    raise ValueError('cached canonical package differs from approved proposal')
        return package, None

    def process(self, job, revision):
        if job['source_id'] in self.accepted:
            receipt = self.accepted[job['source_id']]
            if job['kind'] == 'v123_canonical' and Path(job['inputs']['package']).resolve() != Path(receipt['package_root']).resolve():
                return {'status': 'REVIEW_REQUIRED', 'reason': 'accepted source now points to another package'}
            return {**receipt, 'status': 'ACCEPTED', 'verification_status': 'PASS'}
        if job['kind'] == 'hkdse_pdf':
            package, waiting = self.transcription(job)
            if waiting:
                return waiting
        else:
            package = Path(job['inputs']['package'])
        result = self.preflight(package)
        report = result.report
        if report.batch_id != job['source_id']:
            raise ValueError('source ID does not match package batch')
        if report.status != 'READY FOR USER IMPORT APPROVAL' or result.issues:
            return {'status': 'REVIEW_REQUIRED', 'report': plain(report), 'issues': [plain(x) for x in result.issues]}
        statement = f'USER APPROVED IMPORT BATCH {report.batch_id} {report.preflight_sha256} V1.23 PARENT {report.parent_candidate_digest}'
        approval_path = Path(job.get('import_approval', self.runtime/'absent-approval'))
        actual = approval_path.read_text().strip() if approval_path.is_file() else None
        if actual != statement:
            return {'status': 'AWAITING_IMPORT_APPROVAL', 'reason': 'exact import approval absent or stale',
                    'required_approval': statement, 'report': plain(report), 'package_root': str(package)}
        approval = V123ImportApproval(report.batch_id, report.preflight_sha256, 'V1.23', report.parent_candidate_digest, actual)
        return self.finish_write(package, result, approval, revision)

    def finish_write(self, package, result, approval, revision):
        report = result.report
        batch = V123ApprovedBatch(result, package, approval)
        batches = tuple(self.batches) + (batch,)
        output = safe_runtime(self.runtime/'candidates'/report.preflight_sha256, self.config.repo_root)
        # Durable intent precedes the existing atomic writer. No other append is
        # allowed until this exact operation has a verified durable receipt.
        pending = safe_runtime(self.runtime/'pending-write.json', self.config.repo_root)
        intent = {'package_root':str(package), 'approval':plain(approval), 'revision':revision}
        if pending.exists():
            if read_json(pending) != intent:
                raise ValueError('another writer intent requires recovery')
        else:
            save_json(pending, intent)
        output.parent.mkdir(parents=True, exist_ok=True)
        recovered = output.exists()
        if not recovered:
            build_v123_candidate(V123CandidateBuildRequest(batches, output, self.contract), self.config)
        request = V123CandidateVerificationRequest(output, batches, self.contract)
        verified = verify_v123_candidate(request, self.config)
        if verified.status != 'PASS':
            raise ValueError('candidate verification failed; output preserved')
        manifest = read_json(output/self.contract.manifest_filename)
        receipt = {'status': 'ACCEPTED', 'batch_id': report.batch_id, 'approval': plain(approval),
                   'package_root': str(package), 'candidate_dir': str(output),
                   'candidate_digest': manifest['candidate_digest'], 'ledger': manifest['batch_ledger'],
                   'counts': manifest['counts'], 'verification_status': verified.status,
                   'recovered_existing_output': recovered, 'revision': revision}
        destination = safe_runtime(self.runtime/'receipts'/f'{len(batches):06d}.json', self.config.repo_root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise ValueError('receipt already exists; preserve and investigate')
        save_json(destination, receipt)
        receipt['receipt_path'] = str(destination)
        self.batches, self.parent = list(batches), request
        self.accepted[report.batch_id] = receipt
        pending.unlink()
        return receipt
