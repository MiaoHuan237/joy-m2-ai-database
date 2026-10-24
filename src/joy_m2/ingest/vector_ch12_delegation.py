"""Chapter-only delegated authority; never a fabricated human approval."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import zipfile
from joy_m2.errors import ImportApprovalError

SCOPE_SHA256 = '3468bcaa245a90df3174a76ea9cb300cac5407c9821b322a5b29598969c280e2'
USER_SHA256 = '1a86614c58e0fdcb0b5e8586a2a23264da30d4a992ba035a458af3d956c8993a'
SCOPE_RELATIVE = Path('data/staging/vector-ch12-delegation-20261024-000001/SCOPE_RECORD.json')
INDEX_RELATIVE = Path('data/staging/vector-ch12-intake-20261023-000001/question-review-draft-v2.json')
INDEX_SHA256 = '08edb7ce7d167332c7d5dade49a2533e1c163307440129aeeae4b113d5a6e7bc'


def load_chapter_grant(repo: Path, *, live: bool):
    return _load_grant(repo, repo / SCOPE_RELATIVE, SCOPE_SHA256, USER_SHA256, live=live)


def _load_grant(repo, scope_path, scope_sha256, user_sha256, *, live):
    """Private pin-injected reader for independent synthetic tests.

    Public operational consumers always use load_chapter_grant's fixed pins.
    A returned carrier alone never grants write permission.
    """
    try:
        if not isinstance(repo, Path) or not isinstance(scope_path, Path) or type(live) is not bool:
            _reject('invalid grant arguments')
        content = _read_bound(scope_path, scope_sha256)
        record = _json(content)
        if (record['source_id'] != 'OSM-M2B12-C'
                or record['answer_source_id'] != 'OSM-M2B12-E-ANSWERS'
                or record['target'] != 'V1.24'
                or record['user_authorization_file'] != 'USER_AUTHORIZATION.txt'
                or record['user_authorization_sha256'] != user_sha256):
            _reject('wrong grant identity')
        _read_bound(scope_path.parent/'USER_AUTHORIZATION.txt', user_sha256)
        groups = [record[name] for name in ('authorized_question_ids','excluded_held_ids',
                  'excluded_prerequisite_ids','excluded_accepted_ids')]
        if any(type(g) is not list or any(type(q) is not str or not q for q in g) for g in groups):
            _reject('invalid scope ID sets')
        if tuple(map(len, groups)) != (117,44,8,34) or len(set(sum(groups, []))) != 203:
            _reject('scope partition is not the fixed disjoint 203 units')
        first=record['S04_exact_human_mapping']['question_ids']
        later=record['later_processing_question_ids']
        if len(first)!=14 or len(later)!=103 or set(first+later)!=set(groups[0]) or len(set(first+later))!=117:
            _reject('selected and later scope mismatch')
        for name in ('inventory','progress'):
            _read_bound(Path(record[f'{name}_path']), record[f'{name}_sha256'])
        baseline=record['baseline']
        if baseline['version']!='V1.23' or type(baseline['record_count']) is not int or baseline['record_count']!=677:
            _reject('wrong baseline')
        formal=repo/'releases/V1.23'
        _read_bound(formal/'Joy_M2_Complete_Question_DB_V1_23.sqlite3', baseline['sqlite_sha256'])
        _read_bound(formal/'manifest.json', baseline['manifest_sha256'])
        packages=record['packages']
        if type(packages) is not list or len(packages)!=2:
            _reject('two fixed packages required')
        for role,p in zip(('textbook','answers'),packages):
            if p['role']!=role:
                _reject('package roles exchanged')
            _read_bound(Path(p['path']),p['zip_sha256'],p['zip_size_bytes'])
            m=p['selected_mmd']
            # Only a bounded selected member is read; never extract or execute.
            with zipfile.ZipFile(p['path']) as archive:
                rows=[i for i in archive.infolist() if i.filename==m['member']]
                if len(rows)!=1 or rows[0].file_size!=m['size_bytes'] or rows[0].file_size>16*1024*1024:
                    _reject('selected member identity/size')
                data=archive.read(rows[0])
                if sha256(data).hexdigest()!=m['sha256']:
                    _reject('selected member hash')
        if live:
            marker=scope_path.parent/'REVOKED'
            if marker.exists() or marker.is_symlink():
                _reject('chapter grant revoked')
            for child in (repo/'releases').iterdir():
                match=re.fullmatch(r'V(\d+)\.(\d+)',child.name)
                if match and tuple(map(int,match.groups()))>(1,23):
                    _reject('formal head advanced or ambiguous')
        return ChapterGrant(repo.absolute(),scope_path.absolute(),scope_sha256,content)
    except ImportApprovalError:
        raise
    except (OSError,KeyError,TypeError,ValueError,RuntimeError,zipfile.BadZipFile) as error:
        raise ImportApprovalError('chapter grant evidence is unavailable or invalid') from error


def validate_selection(grant, mapping, accepted_ids):
    try:
        if type(grant) is not ChapterGrant:
            _reject('exact chapter grant required')
        record=_json(grant.scope_bytes)
        if sha256(grant.scope_bytes).hexdigest()!=grant.scope_sha256:
            _reject('grant carrier changed')
        if (mapping['source_id']!=record['source_id'] or
                mapping['answer_source_id']!=record['answer_source_id']):
            _reject('source outside chapter grant')
        packages=[dict(role=p['role'],zip_sha256=p['zip_sha256'],zip_size_bytes=p['zip_size_bytes'],
            selected_member=p['selected_mmd']['member'],member_sha256=p['selected_mmd']['sha256'],
            member_size_bytes=p['selected_mmd']['size_bytes']) for p in record['packages']]
        if _canonical(mapping['packages'])!=_canonical(packages):
            _reject('mapping packages outside fixed identity')
        questions=mapping['questions']
        if type(questions) is not list or not questions:
            _reject('selection must be nonempty')
        ids=tuple(q['question_id'] for q in questions)
        allowed=record['authorized_question_ids']
        if (len(set(ids))!=len(ids) or any(q not in allowed for q in ids)
                or any(q in accepted_ids for q in ids)
                or ids!=tuple(q for q in allowed if q in ids)):
            _reject('unauthorized, duplicate, accepted or out-of-order selection')
        for order,q in enumerate(questions,1):
            expected=f"OSM-M2B12-C-{q['source_section']}-Q{int(q['source_question_number']):02}"
            if (q['question_id']!=expected or type(q['semantic_order']) is not int
                    or q['semantic_order']!=order or str(int(q['source_question_number']))!=q['source_question_number']):
                _reject('stable source identity/order mismatch')
        return ids
    except ImportApprovalError:
        raise
    except (KeyError,ValueError,TypeError) as error:
        raise ImportApprovalError('invalid delegated selection') from error


@dataclass(frozen=True)
class ChapterGrant:
    repo: Path
    scope_path: Path
    scope_sha256: str
    scope_bytes: bytes


def _reject(message):
    raise ImportApprovalError(message)


def _read_bound(path, expected_sha256, expected_size=None):
    if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file():
        _reject('authority file missing or symlinked')
    data=path.read_bytes()
    if (sha256(data).hexdigest()!=expected_sha256 or
            expected_size is not None and (type(expected_size) is not int or len(data)!=expected_size)):
        _reject('authority file identity changed')
    return data


def _json(data):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: _reject('duplicate JSON key')
            result[key]=value
        return result
    return json.loads(data,object_pairs_hook=pairs,
                      parse_constant=lambda _: _reject('nonfinite JSON'))


def _canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()


def _validate_review(review, mapping):
    try:
        keys={'schema_version','executor_id','reviewer_id','mapping_sha256','question_ids',
              'critical','important','conditions_complete','source_unchanged','images_owned',
              'answers_truthful','evidence','limitations'}
        if type(review) is not dict or set(review)!=keys:
            _reject('review fields incomplete or unknown')
        if (review['schema_version']!='vector-ch12-independent-content-review-v1'
                or review['mapping_sha256']!=sha256(_canonical(mapping)).hexdigest()
                or review['question_ids']!=[q['question_id'] for q in mapping['questions']]):
            _reject('review does not bind exact selected mapping')
        if (any(type(review[k]) is not str or not review[k].strip() for k in ('executor_id','reviewer_id'))
                or review['executor_id']==review['reviewer_id']):
            _reject('separate identified reviewer required')
        if any(type(review[k]) is not int or review[k]!=0 for k in ('critical','important')):
            _reject('unresolved independent review findings')
        if any(review[k] is not True for k in ('conditions_complete','source_unchanged','images_owned','answers_truthful')):
            _reject('source quality checks incomplete')
        if (type(review['evidence']) is not list or not review['evidence']
                or any(type(x) is not str or not x.strip() for x in review['evidence'])
                or type(review['limitations']) is not list
                or any(type(x) is not str or not x.strip() for x in review['limitations'])):
            _reject('review evidence/limitations invalid')
    except ImportApprovalError:
        raise
    except (KeyError,TypeError,ValueError) as error:
        raise ImportApprovalError('invalid source review') from error


def _validate_source_anchors(mapping, index):
    try:
        records={r['proposed_question_id']:r for r in index['records']}
        if len(records)!=len(index['records']):
            _reject('source index contains duplicate IDs')
        for q in mapping['questions']:
            origin=records[q['question_id']]
            if any(q[k]!=origin[k] for k in ('source_section','source_question_number')):
                _reject('question ID does not match original source location')
            own=[p['span'] for p in q['question_pieces'] if p['kind']=='source']
            if not own:
                _reject('own question content missing')
            for span in own:
                if (type(span['start_byte']) is not int or type(span['end_byte']) is not int
                        or span['start_byte']>=span['end_byte']
                        or not any(span['package_role']==s['source_role'] and span['member']==s['member']
                            and s['start_byte']<=span['start_byte']<span['end_byte']<=s['end_byte']
                            for s in origin['question_spans'])):
                    _reject('source piece escapes original indexed question')
    except ImportApprovalError:
        raise
    except (KeyError,ValueError,TypeError) as error:
        raise ImportApprovalError('invalid source anchors') from error


def decide_chapter_source(mapping_path, review_path, config):
    """Create a delegated decision only after real source/independent evidence checks."""
    from .vector_ch12_delegated_models import ChapterSourceDecision
    from joy_m2.config import PipelineConfig
    if type(config) is not PipelineConfig:
        _reject('exact PipelineConfig required')
    grant=load_chapter_grant(config.repo_root,live=True)
    if any(not isinstance(p,Path) or p.is_symlink() or not p.is_file() for p in (mapping_path,review_path)):
        _reject('source decision evidence files required')
    decision=ChapterSourceDecision(_canonical(dict(
        schema_version='vector-ch12-delegated-source-decision-v1',
        actor='codex_under_chapter_delegation',grant_sha256=grant.scope_sha256,
        mapping=_json(mapping_path.read_bytes()),review=_json(review_path.read_bytes()))))
    validate_chapter_source_decision(decision,config,live=True)
    return decision


def validate_chapter_source_decision(decision, config, *, live):
    from .vector_ch12_delegated_models import ChapterSourceDecision
    from . import vector_ch12 as source
    from joy_m2.config import PipelineConfig
    if type(config) is not PipelineConfig or type(decision) is not ChapterSourceDecision:
        _reject('exact chapter source decision/config required')
    ChapterSourceDecision(decision.payload)  # Revalidate even forged frozen instances.
    grant=load_chapter_grant(config.repo_root,live=live)
    value=_json(decision.payload)
    if value['grant_sha256']!=grant.scope_sha256:
        _reject('decision refers to untrusted grant')
    mapping=value['mapping']
    validate_selection(grant,mapping,())
    index=_json(_read_bound(config.repo_root/INDEX_RELATIVE,INDEX_SHA256))
    _validate_source_anchors(mapping,index)
    record=_json(grant.scope_bytes)
    paths=[Path(p['path']) for p in record['packages']]
    source._validate_shape(mapping)
    members=source._read_packages(*paths,mapping)
    source._validate_mapping(mapping,members,config)
    source._validate_images(mapping,members)
    return mapping,members


def validate_chapter_canonical(decision, package_root, config, *, live):
    from .vector_ch12 import _canonical_files
    mapping,members=validate_chapter_source_decision(decision,config,live=live)
    if (not isinstance(package_root,Path) or not package_root.is_dir()
            or any(p.is_symlink() for p in (package_root,*package_root.parents))):
        _reject('invalid canonical root')
    config.require_staging_output(package_root)
    expected=_canonical_files(mapping,members)
    files={}
    for path in package_root.rglob('*'):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            _reject('unsafe canonical member')
        if path.is_file(): files[path.relative_to(package_root).as_posix()]=path.read_bytes()
    if files!=expected:
        _reject('canonical differs from delegated source semantics or closure')
    return {name:dict(sha256=sha256(data).hexdigest(),size_bytes=len(data))
            for name,data in sorted(files.items())}


def decide_chapter_import(source_decision, preflight, package_root, config, accepted_ids):
    """Bind an actual READY preflight, never synthesize a human approval."""
    from .vector_ch12_delegated_models import ChapterImportDecision
    grant=load_chapter_grant(config.repo_root,live=True)
    validate_selection(grant,_json(source_decision.payload)['mapping'],accepted_ids)
    closure=validate_chapter_canonical(source_decision,package_root,config,live=True)
    report=preflight.report
    decision=ChapterImportDecision(report.batch_id,report.preflight_sha256,'V1.24',
        report.parent_candidate_digest,
        f'CHAPTER DELEGATED IMPORT BATCH {report.batch_id} {report.preflight_sha256} '
        f'V1.24 PARENT {report.parent_candidate_digest} GRANT {grant.scope_sha256} SOURCE {source_decision.decision_sha256}',
        grant.scope_sha256,source_decision.payload.decode(),_canonical(closure).decode())
    validate_chapter_import(decision,preflight,package_root,config,live=True)
    return decision


def validate_chapter_import(decision, preflight, package_root, config, *, live):
    from dataclasses import fields
    from types import SimpleNamespace
    from .vector_ch12_delegated_models import ChapterImportDecision,ChapterSourceDecision
    from .v124_models import V124ImportPreflightResult
    from .v124_verification import _preflight_payload,_manifest_projection
    from .v124_manifest import load_v124_import_manifest
    if type(decision) is not ChapterImportDecision or type(preflight) is not V124ImportPreflightResult:
        _reject('exact delegated decision/preflight carriers required')
    ChapterImportDecision(**{f.name:getattr(decision,f.name) for f in fields(decision)})
    V124ImportPreflightResult(**{f.name:getattr(preflight,f.name) for f in fields(preflight)})
    source=ChapterSourceDecision(decision.source_decision_json.encode())
    closure=validate_chapter_canonical(source,package_root,config,live=live)
    mapping=_json(source.payload)['mapping'];report=preflight.report
    if (report.status!='READY FOR USER IMPORT APPROVAL' or report.blocking_errors or preflight.issues
            or decision.batch_id!=report.batch_id or decision.batch_id!=mapping['batch_id']
            or decision.preflight_sha256!=report.preflight_sha256
            or decision.parent_candidate_digest!=report.parent_candidate_digest
            or preflight.manifest!=load_v124_import_manifest(package_root/'import_manifest.json')
            or report.manifest_sha256!=sha256(_canonical(_manifest_projection(preflight.manifest))+b'\n').hexdigest()
            or _canonical(closure).decode()!=decision.canonical_closure_json
            or tuple(q['question_id'] for q in mapping['questions'])!=tuple(c.proposed_question_id for c in preflight.candidates)):
        _reject('delegated import does not bind source/canonical/READY preflight')
    # This projection helper only consumes result data, not an approval. No
    # temporary or fabricated manual approval is constructed for reconstruction.
    payload=_preflight_payload(SimpleNamespace(preflight_result=preflight))
    if sha256(_canonical(payload)+b'\n').hexdigest()!=report.preflight_sha256:
        _reject('preflight digest does not reconstruct')
