"""Strict V1.22 canonical package-manifest boundary."""

from dataclasses import fields
import hashlib
import json
from pathlib import Path

from joy_m2.errors import PipelineError

from .models import ImportFileEvidence
from .v122_models import V122BatchImportManifest


__all__ = ("load_v122_import_manifest",)

_GROUP_KINDS = {
    "candidate_records": "candidate_json",
    "source_files": "source",
    "answer_files": "answer",
    "image_files": "image",
    "teacher_notes_files": "teacher_notes",
    "common_errors_files": "common_errors",
}
_ENTRY_FIELDS = ("relative_path", "sha256", "size_bytes", "kind")


class _PairsObject:
    def __init__(self, pairs: list[tuple[str, object]]) -> None:
        self.pairs = tuple(pairs)


def _ordinary_json(value: object) -> object:
    if type(value) is _PairsObject:
        return {key: _ordinary_json(child) for key, child in value.pairs}
    if type(value) is list:
        return [_ordinary_json(child) for child in value]
    return value


def _has_duplicate_keys(value: object) -> bool:
    if type(value) is _PairsObject:
        keys = tuple(key for key, _child in value.pairs)
        return len(keys) != len(set(keys)) or any(
            _has_duplicate_keys(child) for _key, child in value.pairs
        )
    if type(value) is list:
        return any(_has_duplicate_keys(child) for child in value)
    return False


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
    try:
        evidence = ImportFileEvidence(**raw)
    except (TypeError, PipelineError) as exc:
        raise PipelineError(f"{group} entry is invalid") from exc
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


def load_v122_import_manifest(path: Path) -> V122BatchImportManifest:
    """Load one strict V1.22 package manifest from its canonical package root."""
    if not isinstance(path, Path):
        raise PipelineError("manifest path must be a Path")
    try:
        manifest_path = path.resolve(strict=True)
        package_root = manifest_path.parent.resolve(strict=True)
    except OSError as exc:
        raise PipelineError("manifest is missing") from exc
    if (
        path.name != "import_manifest.json"
        or path.is_symlink()
        or not manifest_path.is_file()
        or not package_root.is_dir()
    ):
        raise PipelineError("manifest must be a regular canonical package manifest")
    try:
        raw = manifest_path.read_bytes()
        text = raw.decode("utf-8")
        decoded = json.loads(
            text,
            object_pairs_hook=_PairsObject,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise PipelineError("manifest must be valid strict UTF-8 JSON") from exc
    if _has_duplicate_keys(decoded):
        raise PipelineError("manifest must not contain duplicate keys")
    if type(decoded) is not _PairsObject:
        raise PipelineError("manifest must be a JSON object")
    payload = _ordinary_json(decoded)
    assert type(payload) is dict
    expected_fields = tuple(field.name for field in fields(V122BatchImportManifest))
    if tuple(payload) != expected_fields:
        raise PipelineError("manifest must have exact ordered fields")
    values = dict(payload)
    declared: set[str] = set()
    for group in _GROUP_KINDS:
        raw_group = payload[group]
        if type(raw_group) is not list:
            raise PipelineError(f"{group} must be a JSON array")
        entries = tuple(_load_entry(item, group, package_root) for item in raw_group)
        for entry in entries:
            if entry.relative_path in declared:
                raise PipelineError("manifest file paths must be unique")
            declared.add(entry.relative_path)
        values[group] = entries
    actual: set[str] = set()
    for item in package_root.rglob("*"):
        if item.is_symlink():
            raise PipelineError("package symlinks are not allowed")
        if item.is_file():
            relative = item.relative_to(package_root).as_posix()
            if relative != "import_manifest.json":
                actual.add(relative)
    if actual != declared:
        raise PipelineError("package inventory differs from declared manifest files")
    try:
        return V122BatchImportManifest(**values)
    except (TypeError, PipelineError) as exc:
        raise PipelineError("manifest does not satisfy V1.22 authority") from exc
