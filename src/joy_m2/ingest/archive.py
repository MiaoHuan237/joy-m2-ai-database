"""Safe source inventory for the Task 9B MMD adapter."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata
import zipfile
import zlib

from joy_m2.errors import InputFormatError, InputMissingError

from .adapter_models import (
    MmdAdapterBlockedError,
    MmdAdapterIssue,
    MmdAdapterManifest,
)


_MIB = 1024 * 1024
_ARCHIVE_LIMIT = 50 * _MIB
_MEMBER_COUNT_LIMIT = 256
_TOTAL_LIMIT = 100 * _MIB
_MEMBER_LIMIT = 20 * _MIB
_MMD_LIMIT = 10 * _MIB
_IMAGE_LIMIT = 20 * _MIB
_RATIO_LIMIT = 100
_READ_SIZE = _MIB
_ALLOWED_COMPRESSION = (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
_DRIVE_OR_UNC = re.compile(r"[A-Za-z]:")


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _issue(code: str, field: str, evidence: dict[str, object]) -> MmdAdapterIssue:
    return MmdAdapterIssue(
        code=code,
        severity="blocking",
        proposed_question_id=None,
        source_locator="",
        field=field,
        evidence=_canonical_json(evidence),
    )


def _archive_issue(
    reason: str,
    *,
    actual: object = None,
    limit: object = None,
    member: str | None = None,
) -> MmdAdapterIssue:
    return _issue(
        "archive_integrity_invalid",
        "archive",
        {"actual": actual, "limit": limit, "member": member, "reason": reason},
    )


def _member_issue(raw_name: str, reason: str) -> MmdAdapterIssue:
    return _issue(
        "archive_member_unsafe",
        "archive_member",
        {
            "member_name_sha256": hashlib.sha256(raw_name.encode("utf-8")).hexdigest(),
            "reason": reason,
        },
    )


def _read_file(path: Path) -> bytes:
    content = bytearray()
    try:
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(_READ_SIZE)
                if not chunk:
                    break
                content.extend(chunk)
    except OSError as exc:
        raise InputFormatError("source input is not readable") from exc
    return bytes(content)


def _safe_member_name(raw_name: str, *, directory: bool) -> tuple[str | None, str | None]:
    if (
        raw_name.startswith("//")
        or raw_name.startswith("\\\\")
        or _DRIVE_OR_UNC.match(raw_name) is not None
    ):
        return None, "drive_or_unc"
    if raw_name.startswith("/"):
        return None, "absolute"
    if "\\" in raw_name:
        return None, "backslash"

    parts = raw_name.split("/")
    if directory and parts and parts[-1] == "":
        parts = parts[:-1]
    if ".." in parts:
        return None, "traversal"
    if not parts or any(part in {"", "."} for part in parts):
        return None, "dot_or_empty_component"
    if any(unicodedata.category(character) == "Cc" for character in raw_name):
        return None, "normalized_escape"

    normalized_parts = tuple(unicodedata.normalize("NFC", part) for part in parts)
    canonical = "/".join(normalized_parts) + ("/" if directory else "")
    comparable = canonical[:-1] if directory else canonical
    path = PurePosixPath(comparable)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None, "normalized_escape"
    if path.as_posix() != comparable:
        return None, "normalized_escape"
    return canonical, None


def _is_allowed_metadata(canonical_name: str) -> bool:
    parts = PurePosixPath(canonical_name.rstrip("/")).parts
    if parts and parts[0] == "__MACOSX":
        return True
    basename = parts[-1] if parts else ""
    return basename == ".DS_Store" or basename.startswith("._")


def _hidden_reason(canonical_name: str) -> str | None:
    parts = PurePosixPath(canonical_name.rstrip("/")).parts
    if _is_allowed_metadata(canonical_name):
        allowed_basename = parts[-1]
        for index, part in enumerate(parts):
            if part.startswith(".") and not (
                index == len(parts) - 1
                and (allowed_basename == ".DS_Store" or allowed_basename.startswith("._"))
            ):
                return "hidden"
        return None
    if any(part.startswith(".") for part in parts):
        return "hidden"
    return None


def _entry_type_reason(info: zipfile.ZipInfo) -> str | None:
    if info.create_system != 3:
        return None
    name_is_directory = info.orig_filename.endswith("/")
    mode = info.external_attr >> 16
    kind = stat.S_IFMT(mode)
    if stat.S_ISLNK(mode):
        return "symlink"
    if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
        return "special"
    if name_is_directory and kind not in {0, stat.S_IFDIR}:
        return "special"
    if not name_is_directory and kind == stat.S_IFDIR:
        return "special"
    if not name_is_directory and mode & 0o111:
        return "executable"
    return None


def _is_directory_entry(info: zipfile.ZipInfo) -> bool:
    return info.orig_filename.endswith("/")


def _effective_size_rule(canonical_name: str) -> tuple[str, int]:
    suffix = PurePosixPath(canonical_name).suffix
    if suffix == ".mmd":
        return "mmd_size", _MMD_LIMIT
    if suffix in _IMAGE_SUFFIXES:
        return "image_size", _IMAGE_LIMIT
    return "member_size", _MEMBER_LIMIT


def _read_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    content = bytearray()
    with archive.open(info, "r") as stream:
        while True:
            chunk = stream.read(_READ_SIZE)
            if not chunk:
                break
            content.extend(chunk)
    return bytes(content)


def _stream_member_to_eof(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> int:
    observed = 0
    with archive.open(info, "r") as stream:
        while True:
            chunk = stream.read(_READ_SIZE)
            if not chunk:
                break
            observed += len(chunk)
    return observed


def _zip_source(
    source_path: Path,
    manifest: MmdAdapterManifest,
    raw_size: int,
    initial_issues: tuple[MmdAdapterIssue, ...] = (),
) -> tuple[bytes, bytes | None, dict[str, bytes], tuple[str, ...]]:
    issues = list(initial_issues)
    if raw_size > _ARCHIVE_LIMIT:
        issues.append(
            _archive_issue(
                "archive_size",
                actual=raw_size,
                limit=_ARCHIVE_LIMIT,
            )
        )

    try:
        archive = zipfile.ZipFile(source_path, "r")
        infos = archive.infolist()
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise MmdAdapterBlockedError((_archive_issue("zip_structure"),)) from exc

    with archive:
        if len(infos) > _MEMBER_COUNT_LIMIT:
            issues.append(
                _archive_issue(
                    "member_count",
                    actual=len(infos),
                    limit=_MEMBER_COUNT_LIMIT,
                )
            )

        canonical_by_index: dict[int, str] = {}
        unsafe_indices: set[int] = set()
        for index, info in enumerate(infos):
            raw_name = info.orig_filename
            canonical, reason = _safe_member_name(
                raw_name,
                directory=_is_directory_entry(info),
            )
            if reason is not None:
                issues.append(_member_issue(raw_name, reason))
                unsafe_indices.add(index)
                continue
            assert canonical is not None
            canonical_by_index[index] = canonical

        raw_groups: dict[str, list[int]] = {}
        nfc_groups: dict[str, list[int]] = {}
        casefold_groups: dict[str, list[int]] = {}
        for index, canonical in canonical_by_index.items():
            raw_groups.setdefault(infos[index].orig_filename, []).append(index)
            nfc_groups.setdefault(canonical, []).append(index)
            casefold_groups.setdefault(canonical.casefold(), []).append(index)

        collision_indices: set[int] = set()
        for groups, reason in (
            (raw_groups, "duplicate"),
            (nfc_groups, "nfc_collision"),
            (casefold_groups, "casefold_collision"),
        ):
            for group in groups.values():
                remaining = [index for index in group if index not in collision_indices]
                if len(remaining) > 1:
                    for index in remaining:
                        issues.append(_member_issue(infos[index].orig_filename, reason))
                        collision_indices.add(index)
        unsafe_indices.update(collision_indices)

        total_uncompressed = sum(info.file_size for info in infos)
        if total_uncompressed > _TOTAL_LIMIT:
            issues.append(
                _archive_issue(
                    "total_uncompressed",
                    actual=total_uncompressed,
                    limit=_TOTAL_LIMIT,
                )
            )

        selected = {manifest.primary_member}
        if manifest.answer_member is not None:
            selected.add(manifest.answer_member)

        for index, info in enumerate(infos):
            canonical = canonical_by_index.get(index)
            if canonical is None:
                continue
            type_reason = _entry_type_reason(info)
            if type_reason is not None:
                issues.append(_member_issue(info.orig_filename, type_reason))
                unsafe_indices.add(index)
            hidden_reason = _hidden_reason(canonical)
            if hidden_reason is not None:
                issues.append(_member_issue(info.orig_filename, hidden_reason))
                unsafe_indices.add(index)
            if not _is_directory_entry(info):
                if PurePosixPath(canonical).name.casefold().endswith(".zip"):
                    issues.append(_member_issue(info.orig_filename, "nested_archive"))
                    unsafe_indices.add(index)
                elif PurePosixPath(canonical).suffix.casefold() == ".mmd" and canonical not in selected:
                    issues.append(_member_issue(info.orig_filename, "second_mmd"))
                    unsafe_indices.add(index)
            if info.flag_bits & 0x1:
                issues.append(
                    _archive_issue(
                        "encrypted",
                        actual=True,
                        member=canonical,
                    )
                )
            if info.compress_type not in _ALLOWED_COMPRESSION:
                issues.append(
                    _archive_issue(
                        "compression",
                        actual=info.compress_type,
                        limit=list(_ALLOWED_COMPRESSION),
                        member=canonical,
                    )
                )
            reason, limit = _effective_size_rule(canonical)
            if info.file_size > limit:
                issues.append(
                    _archive_issue(
                        reason,
                        actual=info.file_size,
                        limit=limit,
                        member=canonical,
                    )
                )
            ratio = info.file_size / max(info.compress_size, 1)
            if ratio > _RATIO_LIMIT:
                issues.append(
                    _archive_issue(
                        "compression_ratio",
                        actual=ratio,
                        limit=_RATIO_LIMIT,
                        member=canonical,
                    )
                )

        if not unsafe_indices:
            regular_names = {
                canonical_by_index[index]
                for index, info in enumerate(infos)
                if index in canonical_by_index and not _is_directory_entry(info)
            }
            for field, member in (
                ("primary_member", manifest.primary_member),
                ("answer_member", manifest.answer_member),
            ):
                if member is not None and member not in regular_names:
                    issues.append(
                        _issue(
                            "selection_not_unique",
                            field,
                            {"member": member, "reason": "selected_member_missing"},
                        )
                    )

        if issues:
            raise MmdAdapterBlockedError(tuple(issues))

        stream_issues: list[MmdAdapterIssue] = []
        observed_total = 0
        for index, info in enumerate(infos):
            if _is_directory_entry(info):
                continue
            canonical = canonical_by_index[index]
            try:
                observed = _stream_member_to_eof(archive, info)
            except (OSError, EOFError, RuntimeError, zipfile.BadZipFile, zlib.error) as exc:
                reason = (
                    "crc"
                    if isinstance(exc, zipfile.BadZipFile) and "CRC" in str(exc).upper()
                    else "decompression"
                )
                stream_issues.append(_archive_issue(reason, member=canonical))
                continue
            observed_total += observed
            size_reason, size_limit = _effective_size_rule(canonical)
            if observed > size_limit:
                stream_issues.append(
                    _archive_issue(
                        size_reason,
                        actual=observed,
                        limit=size_limit,
                        member=canonical,
                    )
                )
            observed_ratio = observed / max(info.compress_size, 1)
            if observed_ratio > _RATIO_LIMIT:
                stream_issues.append(
                    _archive_issue(
                        "compression_ratio",
                        actual=observed_ratio,
                        limit=_RATIO_LIMIT,
                        member=canonical,
                    )
                )
        if observed_total > _TOTAL_LIMIT:
            stream_issues.append(
                _archive_issue(
                    "total_uncompressed",
                    actual=observed_total,
                    limit=_TOTAL_LIMIT,
                )
            )
        if stream_issues:
            raise MmdAdapterBlockedError(tuple(stream_issues))

        by_name = {
            canonical_by_index[index]: info
            for index, info in enumerate(infos)
            if not _is_directory_entry(info)
        }
        primary = _read_member(archive, by_name[manifest.primary_member])
        answer = (
            _read_member(archive, by_name[manifest.answer_member])
            if manifest.answer_member is not None
            else None
        )
        selected_images = {
            member
            for selection in manifest.selections
            for member in selection.expected_image_members
        }
        images = {
            member: _read_member(archive, by_name[member])
            for member in selected_images
            if member in by_name
        }
        return primary, answer, images, tuple(sorted(by_name))


def _plain_source(
    source_path: Path,
    manifest: MmdAdapterManifest,
    raw_content: bytes,
    initial_issues: tuple[MmdAdapterIssue, ...] = (),
) -> tuple[bytes, None, dict[str, bytes], tuple[str, ...]]:
    issues = list(initial_issues)
    if len(raw_content) > _MMD_LIMIT:
        issues.append(
            _archive_issue(
                "mmd_size",
                actual=len(raw_content),
                limit=_MMD_LIMIT,
                member=manifest.primary_member,
            )
        )

    root = source_path.parent.resolve(strict=False)
    selected_images = tuple(
        dict.fromkeys(
            member
            for selection in manifest.selections
            for member in selection.expected_image_members
        )
    )
    readable_images: dict[str, Path] = {}
    total_image_size = 0
    for member in selected_images:
        target = source_path.parent / member
        resolved = target.resolve(strict=False)
        expected = root.joinpath(*PurePosixPath(member).parts)
        if not resolved.is_relative_to(root) or resolved != expected:
            issues.append(_member_issue(member, "normalized_escape"))
            continue
        if not target.exists():
            continue
        try:
            mode = target.lstat().st_mode
        except OSError:
            continue
        if stat.S_ISLNK(mode):
            issues.append(_member_issue(member, "symlink"))
            continue
        if not stat.S_ISREG(mode):
            issues.append(_member_issue(member, "special"))
            continue
        size = target.stat().st_size
        total_image_size += size
        if size > _IMAGE_LIMIT:
            issues.append(
                _archive_issue(
                    "image_size",
                    actual=size,
                    limit=_IMAGE_LIMIT,
                    member=member,
                )
            )
        readable_images[member] = target
    if total_image_size > _TOTAL_LIMIT:
        issues.append(
            _archive_issue(
                "total_uncompressed",
                actual=total_image_size,
                limit=_TOTAL_LIMIT,
            )
        )
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))

    images = {member: _read_file(path) for member, path in readable_images.items()}
    return (
        raw_content,
        None,
        images,
        tuple(sorted((manifest.primary_member, *readable_images))),
    )


def read_selected_source(
    manifest: MmdAdapterManifest,
    source_path: Path,
) -> tuple[bytes, bytes | None, dict[str, bytes], tuple[str, ...]]:
    """Validate and selectively read one declared Task 9B source."""

    if not source_path.exists():
        raise InputMissingError("source input does not exist")
    if not source_path.is_file():
        raise InputFormatError("source input must be a regular file")

    raw_content = _read_file(source_path)
    actual_sha256 = hashlib.sha256(raw_content).hexdigest()
    try:
        is_zip = zipfile.is_zipfile(source_path)
    except OSError as exc:
        raise InputFormatError("source input is not readable") from exc

    if not is_zip and raw_content.startswith(b"PK"):
        raise MmdAdapterBlockedError((_archive_issue("zip_structure"),))
    if not is_zip and raw_content.startswith(b"%PDF-"):
        raise MmdAdapterBlockedError(
            (
                _issue(
                    "unsupported_source_format",
                    "source_kind",
                    {
                        "actual": "pdf",
                        "expected": ["mmd", "mmd_zip"],
                        "reason": "top_level_format",
                    },
                ),
            )
        )

    actual_kind = "mmd_zip" if is_zip else "mmd"
    contract_issues: list[MmdAdapterIssue] = []
    if actual_kind != manifest.source_kind:
        contract_issues.append(
            _issue(
                "source_contract_mismatch",
                "$.source_kind",
                {
                    "actual": actual_kind,
                    "expected": manifest.source_kind,
                    "reason": "declared_source_kind_mismatch",
                },
            )
        )
    if actual_sha256 != manifest.source_sha256:
        contract_issues.append(
            _issue(
                "source_contract_mismatch",
                "$.source_sha256",
                {
                    "actual": actual_sha256,
                    "expected": manifest.source_sha256,
                    "reason": "source_digest_mismatch",
                },
            )
        )
    if any(
        json.loads(issue.evidence)["reason"] == "declared_source_kind_mismatch"
        for issue in contract_issues
    ):
        raise MmdAdapterBlockedError(tuple(contract_issues))

    if is_zip:
        return _zip_source(
            source_path,
            manifest,
            len(raw_content),
            tuple(contract_issues),
        )
    return _plain_source(
        source_path,
        manifest,
        raw_content,
        tuple(contract_issues),
    )
