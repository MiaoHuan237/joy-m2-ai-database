"""Deterministic Release-owned hashing and manifest primitives."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from ..errors import PipelineError
from ..models import ArtifactRef


def sha256_bytes(value: bytes) -> str:
    """Return the lowercase SHA-256 digest of exact bytes."""

    if type(value) is not bytes:
        raise PipelineError("SHA-256 input must be bytes")
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash a file without changing it."""

    if not isinstance(path, Path) or not path.is_file():
        raise PipelineError("SHA-256 input must be an existing file")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _reference(path: Path, kind: str) -> ArtifactRef:
    return ArtifactRef(
        path=path,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        kind=kind,
    )


def write_manifest(path: Path, payload: Mapping[str, object]) -> ArtifactRef:
    """Write sorted, indented UTF-8 manifest JSON with one final LF."""

    if not isinstance(path, Path) or not isinstance(payload, Mapping):
        raise PipelineError("manifest requires a Path and a mapping")
    path.write_bytes(
        (
            json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, indent=2)
            + "\n"
        ).encode("utf-8")
    )
    return _reference(path, "manifest")


def write_sha256sums(
    path: Path,
    protected: tuple[ArtifactRef, ...],
) -> ArtifactRef:
    """Write a sorted relative-path SHA256SUMS file."""

    if not isinstance(path, Path) or type(protected) not in {list, tuple}:
        raise PipelineError("SHA256SUMS requires a Path and ArtifactRef sequence")
    root = path.parent.resolve()
    entries: list[tuple[str, ArtifactRef]] = []
    seen: set[str] = set()
    for reference in protected:
        if type(reference) is not ArtifactRef:
            raise PipelineError("protected values must be ArtifactRef instances")
        if reference.kind in {"sha256sums", "zip"}:
            raise PipelineError("SHA256SUMS and ZIP artifacts cannot hash themselves")
        try:
            relative = reference.path.resolve().relative_to(root).as_posix()
        except ValueError as error:
            raise PipelineError("protected artifact must remain below sums directory") from error
        if not relative or relative.startswith("/") or ".." in Path(relative).parts:
            raise PipelineError("protected artifact path is unsafe")
        if relative in seen:
            raise PipelineError("protected artifact paths must be unique")
        if not reference.path.is_file():
            raise PipelineError("protected artifact must exist")
        if (
            reference.size_bytes != reference.path.stat().st_size
            or reference.sha256 != sha256_file(reference.path)
        ):
            raise PipelineError("protected ArtifactRef does not match file bytes")
        seen.add(relative)
        entries.append((relative, reference))
    value = "".join(
        f"{reference.sha256}  {relative}\n"
        for relative, reference in sorted(entries)
    ).encode("utf-8")
    path.write_bytes(value)
    return _reference(path, "sha256sums")
