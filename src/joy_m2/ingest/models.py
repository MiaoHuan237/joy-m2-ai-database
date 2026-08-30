"""Immutable contracts for Task 9 import preflight."""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
from pathlib import PurePosixPath
import re

from joy_m2.errors import PipelineError
from joy_m2.models import ArtifactRef


_SHA256 = re.compile(r"[0-9a-f]{64}")
_KINDS = {"candidate_json", "source", "answer", "image", "teacher_notes", "common_errors"}
_TRANSLATION = {"source_present", "ai_proposed", "verified", "missing"}
_ANSWER = {"source_provided", "ai_solved_verified", "missing_from_source"}
_TAG_DIFFICULTY = {"source_provided", "proposed", "missing"}


def _require_str(value: object, name: str, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        raise PipelineError(f"{name} must be a{' non-empty' if nonempty else ''} string")
    return value


def _require_sha(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise PipelineError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _canonical_relative(value: object, name: str) -> str:
    value = _require_str(value, name)
    path = PurePosixPath(value)
    if path.is_absolute() or "\\" in value or any(part in {"", ".", ".."} for part in path.parts):
        raise PipelineError(f"{name} must be a canonical package-relative POSIX path")
    if path.as_posix() != value:
        raise PipelineError(f"{name} must use canonical POSIX spelling")
    return value


def _exact_tuple(value: object, item_type: type, name: str):
    if type(value) not in {list, tuple}:
        raise PipelineError(f"{name} must be a list or tuple")
    result = tuple(value)
    if any(type(item) is not item_type for item in result):
        raise PipelineError(f"{name} contains an invalid value")
    return result


def _string_tuple(value: object, name: str, *, paths: bool = False):
    if type(value) not in {list, tuple}:
        raise PipelineError(f"{name} must be a list or tuple")
    result = tuple(value)
    for item in result:
        (_canonical_relative if paths else _require_str)(item, name)
    return result


@dataclass(frozen=True)
class ImportFileEvidence:
    relative_path: str
    sha256: str
    size_bytes: int
    kind: str

    def __post_init__(self) -> None:
        _canonical_relative(self.relative_path, "relative_path")
        _require_sha(self.sha256, "sha256")
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise PipelineError("size_bytes must be a non-negative integer")
        if type(self.kind) is not str or self.kind not in _KINDS:
            raise PipelineError("kind is not an approved Task 9A file kind")


@dataclass(frozen=True)
class BatchImportManifest:
    schema_version: str
    batch_id: str
    project: str
    module: str
    chapter: str
    target_release_version: str
    candidate_records: tuple[ImportFileEvidence, ...]
    source_files: tuple[ImportFileEvidence, ...]
    answer_files: tuple[ImportFileEvidence, ...]
    image_files: tuple[ImportFileEvidence, ...]
    teacher_notes_files: tuple[ImportFileEvidence, ...]
    common_errors_files: tuple[ImportFileEvidence, ...]
    language_policy: str
    split_policy: str
    difficulty_policy: str
    tag_policy: str
    answer_policy: str
    explanation_policy: str

    def __post_init__(self) -> None:
        expected = {
            "schema_version": "task9-import-manifest-v1",
            "project": "Joy M2 AI Database", "module": "M2",
            "target_release_version": "V1.19",
            "language_policy": "preserve_source_and_store_reviewed_chinese_separately",
            "split_policy": "one_complete_question_per_record",
            "difficulty_policy": "joy_level_1_5",
            "tag_policy": "controlled_primary_type_and_tags",
            "answer_policy": "preserve_source_answer_identity",
            "explanation_policy": "source_or_independently_verified_with_identity",
        }
        _require_str(self.batch_id, "batch_id")
        _require_str(self.chapter, "chapter")
        for name, required in expected.items():
            if type(getattr(self, name)) is not str or getattr(self, name) != required:
                raise PipelineError(f"{name} must be exactly {required!r}")
        groups = (
            ("candidate_records", "candidate_json"), ("source_files", "source"),
            ("answer_files", "answer"), ("image_files", "image"),
            ("teacher_notes_files", "teacher_notes"),
            ("common_errors_files", "common_errors"),
        )
        seen: set[str] = set()
        for name, kind in groups:
            values = _exact_tuple(getattr(self, name), ImportFileEvidence, name)
            if any(item.kind != kind for item in values):
                raise PipelineError(f"{name} entries must use kind {kind}")
            for item in values:
                if item.relative_path in seen:
                    raise PipelineError("manifest file paths must be unique")
                seen.add(item.relative_path)
            object.__setattr__(self, name, values)


@dataclass(frozen=True)
class ImportAdaptation:
    candidate_id: str
    reference_question_id: str
    adaptation_kind: str
    evidence: str
    reason: str

    def __post_init__(self) -> None:
        _require_str(self.candidate_id, "candidate_id")
        _require_str(self.reference_question_id, "reference_question_id")
        _require_str(self.adaptation_kind, "adaptation_kind")
        _require_str(self.evidence, "evidence")
        _require_str(self.reason, "reason")
        if self.adaptation_kind != "adapted":
            raise PipelineError("adaptation_kind must be exactly 'adapted'")


def _validate_payload_evidence(status: str, payload: str, evidence: str | None, name: str) -> None:
    if status not in _TRANSLATION:
        raise PipelineError(f"{name}_status is invalid")
    if status == "missing":
        if payload != "" or evidence is not None:
            raise PipelineError(f"missing {name} requires empty payload and None evidence")
        return
    if not payload or type(evidence) is not str:
        raise PipelineError(f"{name} requires payload and stable evidence")
    if status == "source_present":
        if not evidence.startswith("source:") or "#" not in evidence[7:]:
            raise PipelineError(f"{name} source evidence is invalid")
        path, locator = evidence[7:].split("#", 1)
        _canonical_relative(path, f"{name}_evidence")
        if not locator:
            raise PipelineError(f"{name} source locator is empty")
    elif status == "ai_proposed":
        prefix = "ai-proposal-sha256:"
        if not evidence.startswith(prefix) or _SHA256.fullmatch(evidence[len(prefix):]) is None:
            raise PipelineError(f"{name} AI proposal evidence is invalid")
        if evidence[len(prefix):] != hashlib.sha256(payload.encode("utf-8")).hexdigest():
            raise PipelineError(f"{name} AI proposal digest does not match payload")
    else:
        prefix = "verified-review-sha256:"
        if not evidence.startswith(prefix) or _SHA256.fullmatch(evidence[len(prefix):]) is None:
            raise PipelineError(f"{name} verified evidence is invalid")


@dataclass(frozen=True)
class ImportCandidate:
    proposed_question_id: str
    source_id: str
    source_question_number: str
    source_section: str
    source_fragment_hash: str
    normalized_text_sha256: str
    question_text_original: str
    question_text_zh: str
    translation_status: str
    translation_evidence: str | None
    solution_original: str
    solution_verified: str
    answer_status: str
    explanation_text: str
    explanation_status: str
    explanation_evidence: str | None
    image_paths: tuple[str, ...]
    image_sha256s: tuple[str, ...]
    image_roles: tuple[str, ...]
    primary_type: str
    tags: tuple[str, ...]
    tag_status: str
    difficulty_level: int | None
    difficulty_status: str
    enrichment_status: str

    def __post_init__(self) -> None:
        for name in ("proposed_question_id", "source_id", "source_question_number", "source_section", "question_text_original", "primary_type"):
            _require_str(getattr(self, name), name)
        _require_sha(self.source_fragment_hash, "source_fragment_hash")
        _require_sha(self.normalized_text_sha256, "normalized_text_sha256")
        for name in ("question_text_zh", "solution_original", "solution_verified", "explanation_text"):
            _require_str(getattr(self, name), name, nonempty=False)
        paths = _string_tuple(self.image_paths, "image_paths", paths=True)
        digests = _string_tuple(self.image_sha256s, "image_sha256s")
        roles = _string_tuple(self.image_roles, "image_roles")
        if not (len(paths) == len(digests) == len(roles)):
            raise PipelineError("image path, digest, and role tuples must have equal length")
        for digest in digests:
            _require_sha(digest, "image_sha256")
        object.__setattr__(self, "image_paths", paths)
        object.__setattr__(self, "image_sha256s", digests)
        object.__setattr__(self, "image_roles", roles)
        object.__setattr__(self, "tags", _string_tuple(self.tags, "tags"))
        if self.answer_status not in _ANSWER:
            raise PipelineError("answer_status is invalid")
        if self.answer_status == "missing_from_source" and (self.solution_original or self.solution_verified):
            raise PipelineError("missing_from_source requires empty solution fields")
        _validate_payload_evidence(self.translation_status, self.question_text_zh, self.translation_evidence, "translation")
        _validate_payload_evidence(self.explanation_status, self.explanation_text, self.explanation_evidence, "explanation")
        if self.tag_status not in _TAG_DIFFICULTY:
            raise PipelineError("tag_status is invalid")
        if (self.tag_status == "missing") != (len(self.tags) == 0):
            raise PipelineError("tag_status must match tag availability")
        if self.difficulty_status not in _TAG_DIFFICULTY:
            raise PipelineError("difficulty_status is invalid")
        if self.difficulty_level is not None and (type(self.difficulty_level) is not int or not 1 <= self.difficulty_level <= 5):
            raise PipelineError("difficulty_level must be an integer from 1 to 5 or None")
        if (self.difficulty_status == "missing") != (self.difficulty_level is None):
            raise PipelineError("difficulty_status must match difficulty availability")
        if self.enrichment_status not in {"complete", "incomplete"}:
            raise PipelineError("enrichment_status is invalid")


@dataclass(frozen=True)
class ImportIssue:
    code: str
    severity: str
    proposed_question_id: str | None
    field: str
    evidence: str

    def __post_init__(self) -> None:
        _require_str(self.code, "code")
        if self.severity not in {"warning", "blocking"}:
            raise PipelineError("severity must be warning or blocking")
        if self.proposed_question_id is not None:
            _require_str(self.proposed_question_id, "proposed_question_id")
        _require_str(self.field, "field")
        _require_str(self.evidence, "evidence")


@dataclass(frozen=True)
class ImportPreflightReport:
    batch_id: str
    status: str
    preflight_sha256: str
    manifest_sha256: str
    baseline_version: str
    before_count: int
    target_release_version: str
    detected_count: int
    new_candidate_count: int
    duplicate_count: int
    rejected_count: int
    ambiguous_count: int
    approved_count: int
    projected_after_count: int
    readable_files: tuple[str, ...]
    unreadable_files: tuple[str, ...]
    unsupported_files: tuple[str, ...]
    teacher_notes_file_count: int
    common_errors_file_count: int
    ambiguous_splits: tuple[str, ...]
    missing_answers: tuple[str, ...]
    missing_explanations: tuple[str, ...]
    incomplete_enrichments: tuple[str, ...]
    missing_images: tuple[str, ...]
    orphan_images: tuple[str, ...]
    level_counts: tuple[tuple[int, int], ...]
    proposed_ids: tuple[str, ...]
    adaptations: tuple[ImportAdaptation, ...]
    warnings: tuple[str, ...]
    blocking_errors: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("batch_id", "baseline_version", "target_release_version"):
            _require_str(getattr(self, name), name)
        _require_sha(self.preflight_sha256, "preflight_sha256")
        _require_sha(self.manifest_sha256, "manifest_sha256")
        if self.baseline_version != "V1.18" or self.target_release_version != "V1.19":
            raise PipelineError("preflight report version identity is invalid")
        if self.status not in {"READY FOR USER IMPORT APPROVAL", "BLOCKED — IMPORT PREFLIGHT FAILED"}:
            raise PipelineError("preflight report status is invalid")
        count_names = ("before_count", "detected_count", "new_candidate_count", "duplicate_count", "rejected_count", "ambiguous_count", "approved_count", "projected_after_count", "teacher_notes_file_count", "common_errors_file_count")
        for name in count_names:
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise PipelineError(f"{name} must be a non-negative integer")
        if self.detected_count != self.new_candidate_count + self.duplicate_count + self.rejected_count:
            raise PipelineError("detected count does not close")
        if self.projected_after_count != self.before_count + self.new_candidate_count:
            raise PipelineError("projected count does not close")
        if self.approved_count != 0 or self.ambiguous_count > self.rejected_count:
            raise PipelineError("preflight approval or ambiguity count is invalid")
        for name in ("readable_files", "unreadable_files", "unsupported_files", "ambiguous_splits", "missing_answers", "missing_explanations", "incomplete_enrichments", "missing_images", "orphan_images", "proposed_ids", "warnings", "blocking_errors"):
            object.__setattr__(self, name, _string_tuple(getattr(self, name), name))
        adaptations = _exact_tuple(self.adaptations, ImportAdaptation, "adaptations")
        object.__setattr__(
            self,
            "adaptations",
            tuple(
                sorted(
                    adaptations,
                    key=lambda adaptation: (
                        adaptation.candidate_id,
                        adaptation.reference_question_id,
                        adaptation.adaptation_kind,
                        adaptation.evidence,
                        adaptation.reason,
                    ),
                )
            ),
        )
        levels = tuple(tuple(value) for value in self.level_counts)
        if any(len(value) != 2 or type(value[0]) is not int or type(value[1]) is not int or not 1 <= value[0] <= 5 or value[1] < 0 for value in levels):
            raise PipelineError("level_counts is invalid")
        if tuple(level for level, _ in levels) != tuple(sorted(level for level, _ in levels)):
            raise PipelineError("level_counts must be sorted")
        object.__setattr__(self, "level_counts", levels)


@dataclass(frozen=True)
class ImportPreflightResult:
    manifest: BatchImportManifest
    baseline_database: ArtifactRef
    candidates: tuple[ImportCandidate, ...]
    issues: tuple[ImportIssue, ...]
    report: ImportPreflightReport

    def __post_init__(self) -> None:
        if type(self.manifest) is not BatchImportManifest or type(self.baseline_database) is not ArtifactRef or type(self.report) is not ImportPreflightReport:
            raise PipelineError("preflight result carrier type is invalid")
        object.__setattr__(self, "candidates", _exact_tuple(self.candidates, ImportCandidate, "candidates"))
        issues = _exact_tuple(self.issues, ImportIssue, "issues")
        object.__setattr__(self, "issues", tuple(sorted(issues, key=lambda issue: (issue.proposed_question_id or "", issue.code, issue.field, issue.evidence))))


def as_plain_dict(value: object) -> dict[str, object]:
    """Project a Task 9 dataclass without inventing aliases."""
    return {field.name: getattr(value, field.name) for field in fields(value)}
