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
