"""Immutable public contracts for the Task 9B Mathpix MMD adapter."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata

from joy_m2.errors import InputFormatError, PipelineError
from joy_m2.ingest.models import BatchImportManifest


_SHA256 = re.compile(r"[0-9a-f]{64}")
_DRIVE_PATH = re.compile(r"[A-Za-z]:")
_SOURCE_LOCATOR = re.compile(r"(.+)#bytes=(0|[1-9][0-9]*):(0|[1-9][0-9]*)")
_KINDS = {"example", "exercise"}
_LANGUAGE_LAYOUTS = {"english_then_chinese", "interleaved_bilingual"}
_ANSWER_MAPPINGS = {"source_answer", "missing_from_source"}
_METADATA_STATUSES = {"source_provided", "proposed", "missing"}
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
_ISSUE_CODES = {
    "source_contract_mismatch",
    "unsupported_source_format",
    "archive_integrity_invalid",
    "archive_member_unsafe",
    "mmd_parse_failed",
    "selection_not_unique",
    "candidate_count_mismatch",
    "language_mapping_ambiguous",
    "image_binding_invalid",
}
_BLOCKED_MESSAGE = "MMD adapter blocked by source diagnostics"


def _require_string(value: object, name: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value):
        raise PipelineError(f"{name} must be an exact non-empty string")
    return value


def _require_enum(value: object, allowed: set[str], name: str) -> str:
    value = _require_string(value, name)
    if value not in allowed:
        raise PipelineError(f"{name} is not an approved value")
    return value


def _canonical_posix_path(value: object, name: str) -> str:
    value = _require_string(value, name)
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value.startswith("//")
        or _DRIVE_PATH.match(value) is not None
        or "\\" in value
        or value == "."
        or any(unicodedata.category(character) == "Cc" for character in value)
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise PipelineError(f"{name} must be a canonical NFC relative POSIX path")
    return value


def _exact_tuple(value: object, item_type: type, name: str):
    if type(value) not in {list, tuple}:
        raise PipelineError(f"{name} must be a list or tuple")
    result = tuple(value)
    if any(type(item) is not item_type for item in result):
        raise PipelineError(f"{name} contains an invalid value")
    return result


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if type(value) not in {list, tuple}:
        raise PipelineError(f"{name} must be a list or tuple")
    result = tuple(value)
    for item in result:
        _require_string(item, name)
    return result


def _contains_absolute_path(value: object) -> bool:
    if type(value) is str:
        return (
            PurePosixPath(value).is_absolute()
            or value.startswith("\\\\")
            or re.match(r"[A-Za-z]:[\\/]", value) is not None
        )
    if type(value) is list:
        return any(_contains_absolute_path(item) for item in value)
    if type(value) is dict:
        return any(
            _contains_absolute_path(key) or _contains_absolute_path(item)
            for key, item in value.items()
        )
    return False


@dataclass(frozen=True)
class MmdSelection:
    proposed_question_id: str
    kind: str
    number: str
    source_section: str
    language_layout: str
    answer_mapping: str
    answer_number: str | None
    expected_image_members: tuple[str, ...]
    primary_type: str
    tags: tuple[str, ...]
    tag_status: str
    difficulty_level: int | None
    difficulty_status: str

    def __post_init__(self) -> None:
        for name in (
            "proposed_question_id",
            "number",
            "source_section",
            "primary_type",
        ):
            _require_string(getattr(self, name), name)
        _require_enum(self.kind, _KINDS, "kind")
        _require_enum(self.language_layout, _LANGUAGE_LAYOUTS, "language_layout")
        _require_enum(self.answer_mapping, _ANSWER_MAPPINGS, "answer_mapping")
        _require_enum(self.tag_status, _METADATA_STATUSES, "tag_status")
        _require_enum(
            self.difficulty_status,
            _METADATA_STATUSES,
            "difficulty_status",
        )

        if self.answer_number is not None:
            _require_string(self.answer_number, "answer_number")
        if self.answer_mapping == "missing_from_source" and self.answer_number is not None:
            raise PipelineError("missing_from_source requires answer_number=None")

        if type(self.expected_image_members) not in {list, tuple}:
            raise PipelineError("expected_image_members must be a list or tuple")
        image_members = tuple(self.expected_image_members)
        for member in image_members:
            member = _canonical_posix_path(member, "expected_image_members")
            member_parts = PurePosixPath(member).parts
            if len(member_parts) < 2 or member_parts[0] != "images":
                raise PipelineError(
                    "expected_image_members must use images/<nonempty-tail> paths"
                )
            if PurePosixPath(member).suffix not in _IMAGE_SUFFIXES:
                raise PipelineError(
                    "expected_image_members must use an exact lowercase image suffix"
                )
        if len(set(image_members)) != len(image_members):
            raise PipelineError("expected_image_members must be unique")
        object.__setattr__(self, "expected_image_members", image_members)

        tags = _string_tuple(self.tags, "tags")
        if (self.tag_status == "missing") != (len(tags) == 0):
            raise PipelineError("tag_status must match tag availability")
        object.__setattr__(self, "tags", tags)

        if self.difficulty_level is not None and (
            type(self.difficulty_level) is not int
            or not 1 <= self.difficulty_level <= 5
        ):
            raise PipelineError("difficulty_level must be an exact integer from 1 to 5 or None")
        if (self.difficulty_status == "missing") != (
            self.difficulty_level is None
        ):
            raise PipelineError("difficulty_status must match difficulty availability")


@dataclass(frozen=True)
class MmdAdapterManifest:
    schema_version: str
    batch_id: str
    source_kind: str
    source_sha256: str
    primary_member: str
    answer_member: str | None
    source_id: str
    chapter: str
    expected_candidate_count: int
    selections: tuple[MmdSelection, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not str or self.schema_version != "task9b-mmd-adapter-v1":
            raise PipelineError("schema_version must be exactly 'task9b-mmd-adapter-v1'")
        for name in ("batch_id", "source_id", "chapter"):
            _require_string(getattr(self, name), name)
        _require_enum(self.source_kind, {"mmd", "mmd_zip"}, "source_kind")
        if type(self.source_sha256) is not str or _SHA256.fullmatch(self.source_sha256) is None:
            raise PipelineError("source_sha256 must be a lowercase SHA-256 digest")

        primary_member = _canonical_posix_path(self.primary_member, "primary_member")
        if PurePosixPath(primary_member).suffix != ".mmd":
            raise PipelineError("primary_member must use the exact lowercase .mmd suffix")
        if self.answer_member is None:
            answer_member = None
        else:
            answer_member = _canonical_posix_path(self.answer_member, "answer_member")
            if PurePosixPath(answer_member).suffix != ".mmd":
                raise PipelineError("answer_member must use the exact lowercase .mmd suffix")
        if answer_member == primary_member:
            raise PipelineError("primary_member and answer_member must differ")
        if self.source_kind == "mmd" and answer_member is not None:
            raise PipelineError("plain MMD input cannot declare an answer_member")

        if type(self.expected_candidate_count) is not int or self.expected_candidate_count < 0:
            raise PipelineError("expected_candidate_count must be an exact non-negative integer")
        selections = _exact_tuple(self.selections, MmdSelection, "selections")
        if self.expected_candidate_count != len(selections):
            raise PipelineError("expected_candidate_count must equal len(selections)")
        proposed_ids = tuple(value.proposed_question_id for value in selections)
        if len(set(proposed_ids)) != len(proposed_ids):
            raise PipelineError("selection proposed_question_id values must be unique")
        if answer_member is None and any(
            value.answer_number is not None for value in selections
        ):
            raise PipelineError("answer_number requires a manifest answer_member")
        object.__setattr__(self, "selections", selections)


@dataclass(frozen=True)
class AdaptedImportPackage:
    package_root: Path
    manifest_path: Path
    manifest: BatchImportManifest

    def __post_init__(self) -> None:
        if not isinstance(self.package_root, Path) or not isinstance(
            self.manifest_path, Path
        ):
            raise PipelineError("package_root and manifest_path must be Path instances")
        if type(self.manifest) is not BatchImportManifest:
            raise PipelineError("manifest must be an exact BatchImportManifest")
        if self.manifest_path != self.package_root / "import_manifest.json":
            raise PipelineError(
                "manifest_path must equal package_root / 'import_manifest.json'"
            )


@dataclass(frozen=True)
class MmdAdapterIssue:
    code: str
    severity: str
    proposed_question_id: str | None
    source_locator: str
    field: str
    evidence: str

    def __post_init__(self) -> None:
        _require_enum(self.code, _ISSUE_CODES, "code")
        if type(self.severity) is not str or self.severity != "blocking":
            raise PipelineError("severity must be exactly 'blocking'")
        if self.proposed_question_id is not None:
            _require_string(self.proposed_question_id, "proposed_question_id")
        _require_string(self.source_locator, "source_locator", allow_empty=True)
        if self.source_locator:
            match = _SOURCE_LOCATOR.fullmatch(self.source_locator)
            if match is None:
                raise PipelineError("source_locator must use the canonical byte-interval form")
            _canonical_posix_path(match.group(1), "source_locator")
            if int(match.group(2)) >= int(match.group(3)):
                raise PipelineError("source_locator must identify a non-empty byte interval")
        _require_string(self.field, "field")
        evidence = _require_string(self.evidence, "evidence")
        try:
            payload = json.loads(
                evidence,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(value)
                ),
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise PipelineError("evidence must be canonical JSON") from exc
        if type(payload) is not dict:
            raise PipelineError("evidence must encode a JSON object")
        try:
            canonical = json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise PipelineError("evidence must be canonical JSON") from exc
        if canonical != evidence:
            raise PipelineError("evidence must use canonical JSON serialization")
        if _contains_absolute_path(payload):
            raise PipelineError("evidence must not contain an absolute runtime path")


class MmdAdapterBlockedError(InputFormatError):
    issues: tuple[MmdAdapterIssue, ...]

    def __init__(self, issues: tuple[MmdAdapterIssue, ...]) -> None:
        validated = _exact_tuple(issues, MmdAdapterIssue, "issues")
        if not validated:
            raise PipelineError("issues must contain at least one MmdAdapterIssue")
        self.issues = tuple(
            sorted(
                validated,
                key=lambda issue: (
                    issue.source_locator,
                    issue.proposed_question_id or "",
                    issue.code,
                    issue.field,
                    issue.evidence,
                ),
            )
        )
        super().__init__(_BLOCKED_MESSAGE)
