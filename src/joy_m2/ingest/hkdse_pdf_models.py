"""Typed authority boundaries for the source-specific HKDSE PP/MS adapter."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path, PurePosixPath
import re

from joy_m2.errors import PipelineError


_SHA256 = re.compile(r"[0-9a-f]{64}")
_METHODS = {"embedded_text", "layout_ocr", "visual_review"}
_STATUSES = {"PROPOSED", "VERIFIED", "REVIEW_REQUIRED"}
_FATAL_CODES = {
    "staging_contract_mismatch",
    "pdf_identity_mismatch",
    "pdf_page_mismatch",
    "extraction_pass_invalid",
}
_REVIEW_CODES = {
    "question_text_missing",
    "official_ms_missing",
    "question_text_mismatch",
    "official_ms_mismatch",
    "subpart_mismatch",
    "mark_mismatch",
    "figure_mismatch",
    "formula_mismatch",
    "page_boundary_ambiguity",
}
_ISSUE_CODES = _FATAL_CODES | _REVIEW_CODES
_ABSOLUTE_DRIVE = re.compile(r"[A-Za-z]:[\\/]")
_BLOCKED_MESSAGE = "HKDSE PDF adapter blocked by source diagnostics"


def _require_str(value: object, name: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value):
        raise PipelineError(f"{name} must be an exact string")
    return value


def _require_positive_int(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise PipelineError(f"{name} must be an exact positive integer")
    return value


def _require_sha(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise PipelineError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _exact_tuple(value: object, item_type: type, name: str) -> tuple:
    if type(value) not in {list, tuple}:
        raise PipelineError(f"{name} must be a list or tuple")
    result = tuple(value)
    if any(type(item) is not item_type for item in result):
        raise PipelineError(f"{name} contains an invalid value")
    return result


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    values = _exact_tuple(value, str, name)
    if any(not item for item in values):
        raise PipelineError(f"{name} contains an empty string")
    return values


def _contains_absolute_path(value: object) -> bool:
    if type(value) is str:
        return (
            PurePosixPath(value).is_absolute()
            or value.startswith("\\\\")
            or _ABSOLUTE_DRIVE.match(value) is not None
        )
    if type(value) is list:
        return any(_contains_absolute_path(item) for item in value)
    if type(value) is dict:
        return any(
            _contains_absolute_path(key) or _contains_absolute_path(item)
            for key, item in value.items()
        )
    return False


def _issue_key(issue: "HkdsePdfTranscriptionIssue") -> tuple[str, str, str, str]:
    return (issue.staging_id or "", issue.code, issue.field, issue.evidence)


@dataclass(frozen=True)
class HkdsePdfPageSpan:
    start_page: int
    end_page: int

    def __post_init__(self) -> None:
        _require_positive_int(self.start_page, "start_page")
        _require_positive_int(self.end_page, "end_page")
        if self.start_page > self.end_page:
            raise PipelineError("page span start must not exceed end")


@dataclass(frozen=True)
class HkdsePdfExtractionRecord:
    staging_id: str
    question_pages: HkdsePdfPageSpan
    ms_pages: HkdsePdfPageSpan
    question_text_original: str
    official_ms_original: str
    subparts: tuple[str, ...]
    marks: int
    figure_references: tuple[str, ...]
    question_method: str
    ms_method: str

    def __post_init__(self) -> None:
        _require_str(self.staging_id, "staging_id")
        if type(self.question_pages) is not HkdsePdfPageSpan:
            raise PipelineError("question_pages must be an exact HkdsePdfPageSpan")
        if type(self.ms_pages) is not HkdsePdfPageSpan:
            raise PipelineError("ms_pages must be an exact HkdsePdfPageSpan")
        _require_str(self.question_text_original, "question_text_original", allow_empty=True)
        _require_str(self.official_ms_original, "official_ms_original", allow_empty=True)
        object.__setattr__(self, "subparts", _string_tuple(self.subparts, "subparts"))
        _require_positive_int(self.marks, "marks")
        object.__setattr__(
            self,
            "figure_references",
            _string_tuple(self.figure_references, "figure_references"),
        )
        if type(self.question_method) is not str or self.question_method not in _METHODS:
            raise PipelineError("question_method is not approved")
        if type(self.ms_method) is not str or self.ms_method not in _METHODS:
            raise PipelineError("ms_method is not approved")


@dataclass(frozen=True)
class HkdsePdfExtractionPass:
    pass_id: str
    staging_sha256: str
    pp_sha256: str
    ms_sha256: str
    records: tuple[HkdsePdfExtractionRecord, ...]

    def __post_init__(self) -> None:
        if type(self.pass_id) is not str or self.pass_id not in {"A", "B"}:
            raise PipelineError("pass_id must be exactly A or B")
        for name in ("staging_sha256", "pp_sha256", "ms_sha256"):
            _require_sha(getattr(self, name), name)
        records = _exact_tuple(self.records, HkdsePdfExtractionRecord, "records")
        identifiers = tuple(record.staging_id for record in records)
        if len(set(identifiers)) != len(identifiers):
            raise PipelineError("extraction record staging_id values must be unique")
        object.__setattr__(self, "records", records)


@dataclass(frozen=True)
class HkdsePdfTranscriptionIssue:
    code: str
    severity: str
    staging_id: str | None
    field: str
    evidence: str

    def __post_init__(self) -> None:
        if type(self.code) is not str or self.code not in _ISSUE_CODES:
            raise PipelineError("code is not an approved Task 10B issue")
        expected_severity = "blocking" if self.code in _FATAL_CODES else "review_required"
        if type(self.severity) is not str or self.severity != expected_severity:
            raise PipelineError("severity does not match the issue code")
        if self.staging_id is not None:
            _require_str(self.staging_id, "staging_id")
        _require_str(self.field, "field")
        evidence = _require_str(self.evidence, "evidence")
        try:
            payload = json.loads(
                evidence,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
            )
        except (ValueError, json.JSONDecodeError) as exc:
            raise PipelineError("evidence must be strict JSON") from exc
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        if evidence != canonical or _contains_absolute_path(payload):
            raise PipelineError("evidence must be canonical JSON without absolute paths")


@dataclass(frozen=True)
class HkdsePdfTranscriptionRecord:
    staging_id: str
    year: int
    section: str
    question_number: int
    question_pages: HkdsePdfPageSpan
    ms_pages: HkdsePdfPageSpan
    question_text_original: str
    official_ms_original: str
    subparts: tuple[str, ...]
    marks: int
    figure_references: tuple[str, ...]
    question_methods: tuple[str, ...]
    ms_methods: tuple[str, ...]
    status: str
    review_reasons: tuple[str, ...]
    module_proposal: str
    topic_proposal: str
    difficulty_proposal: int
    tag_proposals: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_str(self.staging_id, "staging_id")
        _require_positive_int(self.year, "year")
        _require_str(self.section, "section")
        _require_positive_int(self.question_number, "question_number")
        if type(self.question_pages) is not HkdsePdfPageSpan:
            raise PipelineError("question_pages must be an exact HkdsePdfPageSpan")
        if type(self.ms_pages) is not HkdsePdfPageSpan:
            raise PipelineError("ms_pages must be an exact HkdsePdfPageSpan")
        _require_str(self.question_text_original, "question_text_original", allow_empty=True)
        _require_str(self.official_ms_original, "official_ms_original", allow_empty=True)
        object.__setattr__(self, "subparts", _string_tuple(self.subparts, "subparts"))
        _require_positive_int(self.marks, "marks")
        object.__setattr__(
            self,
            "figure_references",
            _string_tuple(self.figure_references, "figure_references"),
        )
        question_methods = _string_tuple(self.question_methods, "question_methods")
        ms_methods = _string_tuple(self.ms_methods, "ms_methods")
        if any(method not in _METHODS for method in (*question_methods, *ms_methods)):
            raise PipelineError("method tuple contains an unapproved method")
        object.__setattr__(self, "question_methods", question_methods)
        object.__setattr__(self, "ms_methods", ms_methods)
        if type(self.status) is not str or self.status not in _STATUSES:
            raise PipelineError("status is not an approved transcription status")
        review_reasons = _string_tuple(self.review_reasons, "review_reasons")
        if self.status == "REVIEW_REQUIRED" and not review_reasons:
            raise PipelineError("REVIEW_REQUIRED needs at least one review reason")
        if self.status != "REVIEW_REQUIRED" and review_reasons:
            raise PipelineError("review reasons require REVIEW_REQUIRED status")
        object.__setattr__(self, "review_reasons", review_reasons)
        _require_str(self.module_proposal, "module_proposal")
        _require_str(self.topic_proposal, "topic_proposal")
        if type(self.difficulty_proposal) is not int or not 1 <= self.difficulty_proposal <= 5:
            raise PipelineError("difficulty_proposal must be an exact integer from 1 to 5")
        object.__setattr__(
            self,
            "tag_proposals",
            _string_tuple(self.tag_proposals, "tag_proposals"),
        )


@dataclass(frozen=True)
class HkdsePdfTranscriptionBatch:
    batch_id: str
    staging_sha256: str
    pp_sha256: str
    ms_sha256: str
    records: tuple[HkdsePdfTranscriptionRecord, ...]
    issues: tuple[HkdsePdfTranscriptionIssue, ...]
    transcription_digest: str
    artifact_root: Path
    transcription_path: Path
    review_path: Path

    def __post_init__(self) -> None:
        _require_str(self.batch_id, "batch_id")
        for name in ("staging_sha256", "pp_sha256", "ms_sha256", "transcription_digest"):
            _require_sha(getattr(self, name), name)
        records = _exact_tuple(self.records, HkdsePdfTranscriptionRecord, "records")
        identifiers = tuple(record.staging_id for record in records)
        if len(set(identifiers)) != len(identifiers):
            raise PipelineError("transcription record staging_id values must be unique")
        issues = _exact_tuple(self.issues, HkdsePdfTranscriptionIssue, "issues")
        if any(issue.severity != "review_required" for issue in issues):
            raise PipelineError("published transcription issues must be review-required")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "issues", tuple(sorted(issues, key=_issue_key)))
        if not isinstance(self.artifact_root, Path):
            raise PipelineError("artifact_root must be a Path")
        if not isinstance(self.transcription_path, Path):
            raise PipelineError("transcription_path must be a Path")
        if not isinstance(self.review_path, Path):
            raise PipelineError("review_path must be a Path")
        if self.transcription_path != self.artifact_root / "transcription.json":
            raise PipelineError("transcription_path must name transcription.json")
        if self.review_path != self.artifact_root / "PDF_TRANSCRIPTION_REVIEW.md":
            raise PipelineError("review_path must name PDF_TRANSCRIPTION_REVIEW.md")

    @property
    def total_questions(self) -> int:
        return len(self.records)

    @property
    def auto_agree_count(self) -> int:
        return sum(record.status == "PROPOSED" for record in self.records)

    @property
    def review_required_count(self) -> int:
        return sum(record.status == "REVIEW_REQUIRED" for record in self.records)

    @property
    def question_complete_count(self) -> int:
        return sum(bool(record.question_text_original) for record in self.records)

    @property
    def ms_complete_count(self) -> int:
        return sum(bool(record.official_ms_original) for record in self.records)

    @property
    def figure_question_count(self) -> int:
        return sum(bool(record.figure_references) for record in self.records)

    @property
    def formula_mismatch_count(self) -> int:
        return sum(issue.code == "formula_mismatch" for issue in self.issues)

    @property
    def page_boundary_ambiguity_count(self) -> int:
        return sum(issue.code == "page_boundary_ambiguity" for issue in self.issues)

    @property
    def missing_content_count(self) -> int:
        return sum(
            issue.code in {"question_text_missing", "official_ms_missing"}
            for issue in self.issues
        )


@dataclass(frozen=True)
class HkdsePdfTranscriptionApproval:
    batch_id: str
    transcription_digest: str
    approval_text: str

    def __post_init__(self) -> None:
        _require_str(self.batch_id, "batch_id")
        _require_sha(self.transcription_digest, "transcription_digest")
        expected = (
            f"USER APPROVED PDF TRANSCRIPTION BATCH {self.batch_id} "
            f"{self.transcription_digest}"
        )
        if type(self.approval_text) is not str or self.approval_text != expected:
            raise PipelineError("approval_text does not exactly bind the transcription")


@dataclass(frozen=True)
class VerifiedHkdsePdfTranscriptionBatch:
    proposal: HkdsePdfTranscriptionBatch
    approval: HkdsePdfTranscriptionApproval
    records: tuple[HkdsePdfTranscriptionRecord, ...]

    def __post_init__(self) -> None:
        if type(self.proposal) is not HkdsePdfTranscriptionBatch:
            raise PipelineError("proposal must be an exact HkdsePdfTranscriptionBatch")
        if type(self.approval) is not HkdsePdfTranscriptionApproval:
            raise PipelineError("approval must be an exact HkdsePdfTranscriptionApproval")
        if (
            self.approval.batch_id != self.proposal.batch_id
            or self.approval.transcription_digest != self.proposal.transcription_digest
        ):
            raise PipelineError("approval does not bind the proposal")
        records = _exact_tuple(self.records, HkdsePdfTranscriptionRecord, "records")
        expected = tuple(replace(record, status="VERIFIED") for record in self.proposal.records)
        if records != expected:
            raise PipelineError("verified records must exactly preserve the approved proposal")
        object.__setattr__(self, "records", records)


class HkdsePdfAdapterBlockedError(PipelineError):
    """Fatal source diagnostic envelope for the HKDSE PDF adapter."""

    def __init__(self, issues: tuple[HkdsePdfTranscriptionIssue, ...]):
        values = _exact_tuple(issues, HkdsePdfTranscriptionIssue, "issues")
        if not values or any(issue.severity != "blocking" for issue in values):
            raise PipelineError("blocked error requires fatal blocking issues")
        self.issues = tuple(sorted(values, key=_issue_key))
        super().__init__(_BLOCKED_MESSAGE)


__all__ = (
    "HkdsePdfPageSpan",
    "HkdsePdfExtractionRecord",
    "HkdsePdfExtractionPass",
    "HkdsePdfTranscriptionIssue",
    "HkdsePdfTranscriptionRecord",
    "HkdsePdfTranscriptionBatch",
    "HkdsePdfTranscriptionApproval",
    "VerifiedHkdsePdfTranscriptionBatch",
    "HkdsePdfAdapterBlockedError",
)
