"""Deterministic Release ZIP packaging."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import zipfile

from ..errors import PipelineError
from ..models import ArtifactRef
from .hashing import sha256_file


def write_deterministic_zip(
    path: Path,
    root: Path,
    artifacts: tuple[ArtifactRef, ...],
    archive_root: str,
) -> ArtifactRef:
    """Package declared files with frozen ZIP metadata and ordering."""

    if not isinstance(path, Path) or not isinstance(root, Path):
        raise PipelineError("ZIP paths must be pathlib.Path values")
    if type(artifacts) not in {list, tuple}:
        raise PipelineError("ZIP artifacts must be an ArtifactRef sequence")
    archive_parts = PurePosixPath(archive_root).parts
    if (
        type(archive_root) is not str
        or not archive_root
        or archive_root.startswith("/")
        or ".." in archive_parts
    ):
        raise PipelineError("archive_root must be a safe relative path")
    resolved_root = root.resolve()
    entries: list[tuple[str, ArtifactRef]] = []
    seen: set[str] = set()
    for reference in artifacts:
        if type(reference) is not ArtifactRef:
            raise PipelineError("ZIP values must be ArtifactRef instances")
        if reference.kind == "zip":
            raise PipelineError("a ZIP cannot contain itself")
        try:
            relative = reference.path.resolve().relative_to(resolved_root).as_posix()
        except ValueError as error:
            raise PipelineError("ZIP artifact must remain below package root") from error
        if relative in seen or not relative or ".." in PurePosixPath(relative).parts:
            raise PipelineError("ZIP artifact paths must be unique and safe")
        if not reference.path.is_file() or (
            reference.size_bytes != reference.path.stat().st_size
            or reference.sha256 != sha256_file(reference.path)
        ):
            raise PipelineError("ZIP ArtifactRef does not match file bytes")
        seen.add(relative)
        entries.append((relative, reference))

    with zipfile.ZipFile(
        path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for relative, reference in sorted(entries):
            info = zipfile.ZipInfo(
                f"{archive_root}/{relative}",
                (1980, 1, 1, 0, 0, 0),
            )
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(
                info,
                reference.path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
    return ArtifactRef(
        path=path,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        kind="zip",
    )
