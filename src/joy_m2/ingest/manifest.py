"""Exact Task 9A manifest decoding and read-only package inventory checks."""

from __future__ import annotations

from dataclasses import fields
import hashlib
import json
from pathlib import Path

from joy_m2.errors import PipelineError

from .models import BatchImportManifest, ImportFileEvidence


_GROUP_KINDS = {
    "candidate_records": "candidate_json", "source_files": "source",
    "answer_files": "answer", "image_files": "image",
    "teacher_notes_files": "teacher_notes", "common_errors_files": "common_errors",
}
_ENTRY_FIELDS = ("relative_path", "sha256", "size_bytes", "kind")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise PipelineError("declared package file is unreadable") from exc
    return digest.hexdigest()


def _load_entry(raw: object, group: str, package_root: Path) -> ImportFileEvidence:
    if type(raw) is not dict or tuple(raw) != _ENTRY_FIELDS:
        raise PipelineError(f"{group} entry must have exact ordered fields")
    evidence = ImportFileEvidence(**raw)
    if evidence.kind != _GROUP_KINDS[group]:
        raise PipelineError(f"{group} has the wrong file kind")
    path = package_root / evidence.relative_path
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise PipelineError("declared package file is missing") from exc
    if path.is_symlink() or not resolved.is_relative_to(package_root) or not resolved.is_file():
        raise PipelineError("declared package file is unsafe or not a regular file")
    try:
        size = resolved.stat().st_size
    except OSError as exc:
        raise PipelineError("declared package file is unreadable") from exc
    if size != evidence.size_bytes:
        raise PipelineError("declared package file size does not match")
    if _hash_file(resolved) != evidence.sha256:
        raise PipelineError("declared package file SHA-256 does not match")
    return evidence


def load_import_manifest(path: Path, package_root: Path) -> BatchImportManifest:
    """Load one exact manifest while retaining only canonical relative evidence."""
    if not isinstance(path, Path) or not isinstance(package_root, Path):
        raise PipelineError("manifest path and package_root must be Paths")
    try:
        root = package_root.resolve(strict=True)
        manifest_path = path.resolve(strict=True)
    except OSError as exc:
        raise PipelineError("manifest or package root is missing") from exc
    if not root.is_dir() or path.is_symlink() or not manifest_path.is_relative_to(root) or not manifest_path.is_file():
        raise PipelineError("manifest must be a regular file within package_root")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PipelineError("manifest must be valid UTF-8 JSON") from exc
    expected_fields = tuple(field.name for field in fields(BatchImportManifest))
    if type(payload) is not dict or tuple(payload) != expected_fields:
        raise PipelineError("manifest must have exact ordered fields")
    values = dict(payload)
    declared: set[str] = set()
    for group in _GROUP_KINDS:
        raw_group = payload[group]
        if type(raw_group) is not list:
            raise PipelineError(f"{group} must be a JSON array")
        entries = tuple(_load_entry(item, group, root) for item in raw_group)
        for entry in entries:
            if entry.relative_path in declared:
                raise PipelineError("manifest file paths must be unique")
            declared.add(entry.relative_path)
        values[group] = entries
    manifest_relative = manifest_path.relative_to(root).as_posix()
    actual: set[str] = set()
    for item in root.rglob("*"):
        if item.is_symlink():
            raise PipelineError("package symlinks are not allowed")
        if item.is_file():
            relative = item.relative_to(root).as_posix()
            if relative != manifest_relative:
                actual.add(relative)
    if actual != declared:
        raise PipelineError("package inventory differs from declared manifest files")
    return BatchImportManifest(**values)
