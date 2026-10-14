"""Explicit-file, local checkpoint archives; restore never writes original paths."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile
from .automation import canonical, safe_runtime, sha
from .hkdse_pdf_adapter import atomic_rename_no_replace


def _plain_path(path):
    path=Path(path).absolute()
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('symlink checkpoint path')
    return path


def _require_static_files(sources):
    # Byte archives are not live SQLite backups. Never checkpoint source data;
    # conservatively reject even empty sidecars and check again after reading.
    for source in sources:
        for suffix in ('-wal','-journal','-shm'):
            sidecar=Path(str(source)+suffix)
            if sidecar.exists() or sidecar.is_symlink():
                raise ValueError(f'SQLite sidecar requires a closed static source: {sidecar}')


def _verify(archive):
    names=archive.namelist()
    if len(names)!=len(set(names)) or 'manifest.json' not in names:
        raise ValueError('invalid archive members')
    manifest=json.loads(archive.read('manifest.json'))
    if manifest.get('schema_version')!='joy-ingestion-backup-v1':
        raise ValueError('unknown checkpoint schema')
    files=manifest['files']
    expected={'manifest.json'}|{f'files/{i:08d}' for i in range(len(files))}
    if set(names)!=expected: raise ValueError('archive closure mismatch')
    for i,row in enumerate(files):
        name=f'files/{i:08d}'
        if row['member']!=name: raise ValueError('unsafe archive member')
        raw=archive.read(name)
        if len(raw)!=row['size_bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('archive identity mismatch')
    return manifest

def create_backup(files, archive_path, repo_root):
    repo=Path(repo_root).resolve(strict=True)
    output=_plain_path(archive_path)
    if output.exists(): raise FileExistsError(output)
    runtime=safe_runtime(repo/'data/staging/auto-ingestion',repo)
    runtime.mkdir(parents=True,exist_ok=True)
    lockpath=safe_runtime(runtime/'cycle.lock',repo)
    with lockpath.open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        sources=sorted({_plain_path(p) for p in files})
        if not sources or any(not p.is_file() or p==output for p in sources):
            raise ValueError('checkpoint requires explicit existing files')
        _require_static_files(sources)
        output.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
            path=Path(temporary)/'checkpoint.zip'
            rows=[]
            with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_STORED) as archive:
                for i,source in enumerate(sources):
                    raw=source.read_bytes()
                    row={'original_path':str(source),'member':f'files/{i:08d}',
                         'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
                    archive.writestr(row['member'],raw)
                    rows.append(row)
                archive.writestr('manifest.json',canonical({'schema_version':'joy-ingestion-backup-v1','files':rows}))
            # Fail if a source changed during snapshot; no inconsistent checkpoint.
            if any(sha(p)!=row['sha256'] for p,row in zip(sources,rows)):
                raise ValueError('source changed during checkpoint')
            _require_static_files(sources)
            with zipfile.ZipFile(path) as archive: _verify(archive)
            with path.open('rb') as handle: os.fsync(handle.fileno())
            atomic_rename_no_replace(path,output)
    return {'archive_path':str(output),'sha256':sha(output),'file_count':len(rows),
            'off_device':False}


def restore_backup(archive_path, output_dir):
    source=_plain_path(archive_path)
    output=_plain_path(output_dir)
    if output.exists(): raise FileExistsError(output)
    if {'releases','baselines'} & set(output.parts):
        raise ValueError('restore cannot target formal artifact directories')
    with zipfile.ZipFile(source) as archive:
        manifest=_verify(archive)
        output.parent.mkdir(parents=True,exist_ok=True)
        temporary=Path(tempfile.mkdtemp(prefix='.recovery-',dir=output.parent))
        try:
            (temporary/'files').mkdir()
            for row in manifest['files']:
                path=temporary/row['member']
                with path.open('xb') as handle:
                    handle.write(archive.read(row['member']))
                    handle.flush()
                    os.fsync(handle.fileno())
            (temporary/'manifest.json').write_text(canonical(manifest)+'\n',encoding='utf-8')
            atomic_rename_no_replace(temporary,output)
        finally:
            if temporary.exists(): shutil.rmtree(temporary)
    return {'restore_root':str(output),'file_count':len(manifest['files']),'verified':True}
