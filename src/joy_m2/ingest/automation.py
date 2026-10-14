"""Approval-preserving operational orchestration (not formal data authority)."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def safe_runtime(path, root):
    path = Path(path).absolute()
    root = Path(root).absolute()
    if not path.is_relative_to(root):
        raise ValueError('runtime outside allowed root')
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError('symlink runtime is forbidden')
        if item == root:
            break
    return path


def save_json(path, value):
    """Replace only a runner-owned journal/report, not a source artifact."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError('symlink report')
    temporary = path.with_name(path.name + '.tmp')
    if temporary.is_symlink():
        raise ValueError('symlink temporary report')
    with temporary.open('w', encoding='utf-8') as f:
        f.write(canonical(value) + '\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def fingerprint(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('input symlink not accepted: ' + str(path))
    if not path.exists():
        return {'missing': str(path)}
    if path.is_file():
        return {'path': str(path), 'sha256': sha(path)}
    return [fingerprint(p) for p in sorted(path.rglob('*')) if p.is_file() or p.is_symlink()]


def inventory(roots, runtime):
    rows = []
    for directory in sorted(set(roots)):
        root = Path(directory)
        if not root.is_dir():
            rows.append({'path': str(root), 'sha256': None, 'record_count': None, 'error': 'source root missing'})
            continue
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in ('.json','.pdf','.md','.mmd','.zip'):
                continue
            if path.is_relative_to(runtime):
                continue
            row = {'path': str(path), 'sha256': None, 'record_count': None, 'error': None}
            try:
                if path.is_symlink():
                    raise ValueError('source symlink')
                row['sha256'] = sha(path)
                if path.suffix.lower() != '.json':
                    row['state'] = 'SOURCE_NOT_PARSED'
                    rows.append(row)
                    continue
                data = read_json(path)
                row['source_id'] = data.get('batch_id') if isinstance(data, dict) else None
                records = data.get('records') if isinstance(data, dict) else None
                if isinstance(records, list):
                    row['record_count'] = len(records)
                    row['text_fields_present'] = sum(bool(r.get('question_text_original')) for r in records if isinstance(r, dict))
                row['state'] = 'DISCOVERED_NOT_APPROVED'
            except (ValueError, OSError) as exc:
                row['error'] = str(exc)
            rows.append(row)
    return rows


def assess_draft(job):
    result = {'status': 'REVIEW_REQUIRED', 'reason': 'unsupported source profile; HKDSE adapter requires public_exam_question and HKDSE-YYYY-M2-Qxx, not a mock-paper identity'}
    if job['kind'] != 'structured_draft':
        return result
    data = read_json(job['inputs']['staging'])
    if data.get('batch_id') != job['source_id']:
        raise ValueError('draft/source ID mismatch')
    records = data['records']
    result.update(record_count=len(records),
                  text_field_count=sum(bool(r.get('question_text_original')) for r in records),
                  answer_outline_count=sum(bool(r.get('solution_outline_zh')) for r in records),
                  official_ms_verified_count=0, source_identity_checks=[])
    for key, role in (('question_file', 'pp'), ('solution_file', 'ms')):
        declared = data.get('source', {}).get(key)
        if declared:
            path = job['inputs'].get(role)
            actual = sha(path) if path and Path(path).is_file() else None
            result['source_identity_checks'].append({'role':role, 'path':path,
                'declared_sha256':declared.get('sha256'), 'actual_sha256':actual,
                'matched':actual is not None and actual==declared.get('sha256')})
    return result


def run_cycle(config_path: Path, repo_root: Path) -> dict:
    repo = Path(repo_root).resolve(strict=True)
    config = read_json(config_path)
    jobs = config['jobs']
    ids = [j['source_id'] for j in jobs]
    if any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError('jobs require distinct stable source IDs')
    runtime = safe_runtime(repo/'data/staging/auto-ingestion', repo)
    runtime.mkdir(parents=True, exist_ok=True)
    for name in ('cycle.lock', 'state.sqlite3', 'last_run.json'):
        safe_runtime(runtime/name, repo)
    with (runtime/'cycle.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'BUSY', 'processed': 0, 'model_calls': 0}
        dbpath = runtime/'state.sqlite3'
        existing = dbpath.exists()
        with sqlite3.connect(dbpath) as db:
            if existing and db.execute('PRAGMA application_id').fetchone()[0] != 1246645553:
                raise ValueError('not an ingestion journal')
            db.execute('PRAGMA application_id=1246645553')
            db.execute('CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS jobs (source_id TEXT, revision TEXT, attempts INTEGER, status TEXT, result TEXT, PRIMARY KEY(source_id,revision))')
            db.commit()
            rows = inventory(config['inventory_roots'], runtime)
            old = db.execute('SELECT payload FROM snapshots WHERE id=1').fetchone()
            old = json.loads(old[0]) if old else {}
            before = {x['path']: x for x in old.get('inventory', [])}
            now = {x['path']: x for x in rows}
            receipts = [str(Path(p).resolve()) for p in config['receipts']]
            def current_context():
                own_receipts = sorted((runtime/'receipts').glob('*.json'))
                context = [fingerprint(p) for p in (*receipts, *own_receipts)]
                context.append(fingerprint(runtime/'pending-write.json'))
                context.extend(fingerprint(runtime/name) for name in ('proposals', 'packages'))
                context.extend(fingerprint(p) for p in sorted((repo/'data/staging').glob('task13-v123*/**/REAL_BATCH_IMPORT_RECEIPT.json')))
                if any(j['kind'] in ('hkdse_pdf', 'v123_canonical') for j in jobs):
                    context.append(fingerprint(repo/'releases/V1.22'))
                # Bind full verified prefix/package trees, not just receipt text.
                for p in (*receipts, *own_receipts):
                    data = read_json(p)
                    for name in ('candidate_dir', 'package_root'):
                        if name in data:
                            context.append(fingerprint(data[name]))
                return context
            context = current_context()
            output = []
            processed = 0
            operations = None
            write_blocked = False
            for job in jobs:
                paths = dict(job.get('inputs', {}))
                paths.update({k: job[k] for k in ('transcription_approval', 'import_approval') if job.get(k)})
                try:
                    watched = {k: fingerprint(v) for k, v in paths.items()}
                    watch_error = None
                except (ValueError, OSError) as exc:
                    watched, watch_error = {}, str(exc)
                revision = hashlib.sha256(canonical([job, watched, context, watch_error]).encode()).hexdigest()
                input_identity = hashlib.sha256(canonical([job, watched]).encode()).hexdigest()
                saved = db.execute('SELECT attempts,status,result FROM jobs WHERE source_id=? AND revision=?', (job['source_id'], revision)).fetchone()
                if write_blocked and job['kind'] in ('hkdse_pdf','v123_canonical'):
                    result = {'status':'REVIEW_REQUIRED', 'reason':'pending writer recovery; later writes disabled'}
                elif saved and not (runtime/'pending-write.json').exists() and (saved[1] != 'FAILED' or saved[0] >= 3):
                    result = json.loads(saved[2])
                else:
                    processed += 1
                    accepted = db.execute("SELECT result FROM jobs WHERE source_id=? AND status='ACCEPTED'", (job['source_id'],)).fetchone()
                    try:
                        if watch_error:
                            raise ValueError(watch_error)
                        if any(not Path(p).exists() for p in job.get('inputs', {}).values()):
                            raise FileNotFoundError('one or more declared inputs are missing')
                        if accepted and json.loads(accepted[0]).get('input_identity') != input_identity:
                            result = {'status': 'REVIEW_REQUIRED', 'reason': 'accepted source changed or parent advanced; use existing receipt, never auto-reimport', 'prior_receipt': json.loads(accepted[0])}
                        elif job['kind'] not in ('hkdse_pdf', 'v123_canonical'):
                            result = assess_draft(job)
                        else:
                            from joy_m2.ingest.automation_v123 import V123Operations
                            if operations is None:
                                operations = V123Operations(repo, runtime, receipts)
                            result = operations.process(job, revision)
                    except Exception as exc:
                        result = {'status': 'FAILED', 'error_type': type(exc).__name__, 'reason': str(exc)}
                        if (runtime/'pending-write.json').exists():
                            write_blocked = True
                    result['input_identity'] = input_identity
                    context = current_context()
                    # Never label post-verification mutations as verified bytes.
                    # First successful publication gets a fresh verification on
                    # the next cycle; only non-accepted preparation can converge
                    # immediately to its newly generated cache context.
                    if result['status'] != 'ACCEPTED':
                        revision = hashlib.sha256(canonical([job, watched, context, watch_error]).encode()).hexdigest()
                    with db:
                        db.execute('INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?)',
                                   (job['source_id'], revision, saved[0]+1 if saved else 1, result['status'], canonical(result)))
                output.append({'source_id': job['source_id'], 'revision': revision, 'result': result})
            snapshot = {'inventory': rows, 'jobs': output, 'context': context}
            report = {'status': 'COMPLETE', 'no_change': snapshot == old and processed == 0,
                      'discovered': len(now.keys()-before.keys()),
                      'changed': sum(now[p] != before[p] for p in now.keys() & before.keys()),
                      'missing': len(before.keys()-now.keys()), 'processed': processed,
                      'model_calls': 0, 'new_questions': None,
                      'unique_contents': len({x['sha256'] for x in rows if x['sha256']}),
                      'failed': sum(j['result']['status']=='FAILED' for j in output),
                      'pending_review': sum(j['result']['status'] in ('REVIEW_REQUIRED','AWAITING_TRANSCRIPTION_APPROVAL','AWAITING_IMPORT_APPROVAL') for j in output),
                      'accepted': sum(j['result']['status']=='ACCEPTED' for j in output),
                      'inventory': rows, 'jobs': output}
            with db:
                db.execute('INSERT OR REPLACE INTO snapshots VALUES (1,?)', (canonical(snapshot),))
            save_json(runtime/'last_run.json', report)
            return report
