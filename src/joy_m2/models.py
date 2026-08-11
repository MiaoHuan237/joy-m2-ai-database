"""Immutable values shared by the maintained Joy M2 pipeline layers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Literal

from . import config as _config
from .errors import AuditBlockedError, PipelineError


AuditProfile = Literal["V1.17", "V1.18"]


def _tuple_of_tuples(values):
    return tuple(tuple(value) for value in values)


@dataclass(frozen=True)
class ReleaseSpec:
    release_version: str
    baseline_version: str
    baseline_sqlite_sha256: str
    schema_version: str
    created_at: str


@dataclass(frozen=True)
class ApprovalRecord:
    release_version: str
    candidate_manifest_sha256: str
    approved_by: str
    approved_at: str
    scope: str


@dataclass(frozen=True)
class ArtifactRef:
    path: Path
    sha256: str
    size_bytes: int
    kind: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", self.path.resolve())


@dataclass(frozen=True)
class AuditIssue:
    code: str
    severity: str
    question_id: str
    field: str
    evidence: str


@dataclass(frozen=True)
class Correction:
    field: str
    error_origin: str
    original: str
    corrected: str
    reason: str
    evidence: str


@dataclass(frozen=True)
class PublicationEvidence:
    record_status: str
    joy_approval: str
    approved_at: str | None


@dataclass(frozen=True)
class QuestionImage:
    path: str
    sha256: str | None
    role: str | None

    def __post_init__(self) -> None:
        if type(self.path) is not str or not self.path:
            raise PipelineError("question image path must be a non-empty string")
        if self.sha256 is not None and (
            type(self.sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None
        ):
            raise PipelineError("question image sha256 must be a lowercase SHA-256 digest")
        if self.role is not None and (type(self.role) is not str or not self.role):
            raise PipelineError("question image role must be a non-empty string")
        if (self.sha256 is None) != (self.role is None):
            raise PipelineError("question image sha256 and role must be provided together")


@dataclass(frozen=True)
class AuditedQuestion:
    question_id: str
    source_id: str
    source_question_number: str
    source_section: str
    source_file: str
    source_member: str
    source_sha256: str
    source_member_sha256: str
    source_fragment_hash: str
    source_page: str
    solution_source_file: str
    solution_source_member: str
    solution_source_member_sha256: str
    question_text_original: str
    question_text_zh: str
    question_text_zh_reviewed: str
    question_latex: str
    marks_total: int | None
    year: int | None
    image_paths: tuple[QuestionImage, ...]
    solution_original: str
    solution_verified: str
    answer_status: str
    answer_verification_status: str
    official_marking_available: bool
    primary_type: str
    tags: tuple[str, ...]
    difficulty_level: int
    difficulty_evidence: str
    difficulty_dimensions: tuple[tuple[str, int], ...]
    old_difficulty: int
    old_difficulty_label: str
    old_tags: tuple[str, ...]
    question_review_status: str
    formula_review_status: str
    image_review_status: str
    answer_review_status: str
    correction_status: str
    corrections: tuple[Correction, ...]
    duplicate_status: str
    duplicate_reference: str
    duplicate_evidence: str
    audit_notes: str
    review_checks: tuple[tuple[str, str], ...]
    unresolved_issues: tuple[str, ...]
    publication_evidence: PublicationEvidence
    audited_at: str
    schema_version: str
    source_heading: str

    def __post_init__(self) -> None:
        for field_name in ("marks_total", "year"):
            value = getattr(self, field_name)
            if value is not None and type(value) is not int:
                raise PipelineError(f"{field_name} must be an integer or None")
        if type(self.image_paths) not in {list, tuple}:
            raise PipelineError("image_paths must be a list or tuple of QuestionImage values")
        image_paths = tuple(self.image_paths)
        if any(type(image) is not QuestionImage for image in image_paths):
            raise PipelineError("image_paths must contain only QuestionImage values")
        object.__setattr__(self, "image_paths", image_paths)
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(
            self,
            "difficulty_dimensions",
            _tuple_of_tuples(self.difficulty_dimensions),
        )
        object.__setattr__(self, "old_tags", tuple(self.old_tags))
        object.__setattr__(self, "corrections", tuple(self.corrections))
        object.__setattr__(self, "review_checks", _tuple_of_tuples(self.review_checks))
        object.__setattr__(self, "unresolved_issues", tuple(self.unresolved_issues))


@dataclass(frozen=True)
class Task4Compatibility:
    task4_resolution_present: bool
    task4_resolution: str | None
    task4_processed_at_present: bool
    task4_processed_at: str | None

    def __post_init__(self) -> None:
        pairs = (
            (
                "task4_resolution",
                self.task4_resolution_present,
                self.task4_resolution,
            ),
            (
                "task4_processed_at",
                self.task4_processed_at_present,
                self.task4_processed_at,
            ),
        )
        for name, present, value in pairs:
            if type(present) is not bool:
                raise PipelineError(f"{name}_present must be a boolean")
            if value is not None and type(value) is not str:
                raise PipelineError(f"{name} must be a string or None")
            if not present and value is not None:
                raise PipelineError(f"{name} must be None when its key is absent")


@dataclass(frozen=True)
class ReleaseCompatibility:
    formal_release_version: str
    selectable: bool
    source_order: int

    def __post_init__(self) -> None:
        if type(self.formal_release_version) is not str:
            raise PipelineError("formal_release_version must be a string")
        if type(self.selectable) is not bool:
            raise PipelineError("selectable must be a boolean")
        if type(self.source_order) is not int:
            raise PipelineError("source_order must be an integer")


@dataclass(frozen=True)
class AuditedRecord:
    question: AuditedQuestion
    task4_compatibility: Task4Compatibility | None
    release_compatibility: ReleaseCompatibility | None

    def __post_init__(self) -> None:
        if type(self.question) is not AuditedQuestion:
            raise PipelineError("question must be an AuditedQuestion")
        if self.task4_compatibility is not None and (
            type(self.task4_compatibility) is not Task4Compatibility
        ):
            raise PipelineError("task4_compatibility must be Task4Compatibility or None")
        if self.release_compatibility is not None and (
            type(self.release_compatibility) is not ReleaseCompatibility
        ):
            raise PipelineError(
                "release_compatibility must be ReleaseCompatibility or None"
            )
        if (self.task4_compatibility is None) == (self.release_compatibility is None):
            raise PipelineError("exactly one compatibility carrier must be provided")


@dataclass(frozen=True)
class AuditedBatch:
    records: tuple[AuditedRecord, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))


@dataclass(frozen=True)
class AuditResult:
    records: tuple[AuditedRecord, ...]
    issues: tuple[AuditIssue, ...]
    answer_status_counts: tuple[tuple[str, int], ...]
    status: str

    def __post_init__(self) -> None:
        records = tuple(self.records)
        issues = tuple(self.issues)
        answer_status_counts = _tuple_of_tuples(self.answer_status_counts)
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "issues", issues)
        object.__setattr__(self, "answer_status_counts", answer_status_counts)

        has_blocker = any(issue.severity == "blocker" for issue in issues)
        expected_status = "FAIL" if has_blocker else "PASS"
        if self.status != expected_status:
            raise PipelineError(
                f"audit status {self.status!r} is inconsistent with blocking issues"
            )

        declared_counts: dict[str, int] = {}
        for entry in answer_status_counts:
            if len(entry) != 2:
                raise PipelineError("answer_status_counts entries must contain two values")
            answer_status, count = entry
            if type(answer_status) is not str:
                raise PipelineError("answer status names must be strings")
            if type(count) is not int or count <= 0:
                raise PipelineError("answer status counts must be positive integers")
            if answer_status in declared_counts:
                raise PipelineError("answer status classifications must be unique")
            declared_counts[answer_status] = count
        actual_counts = Counter(record.question.answer_status for record in records)
        if declared_counts != actual_counts:
            raise PipelineError(
                "answer_status_counts is inconsistent with audited records"
            )

    def require_passed(self) -> AuditedBatch:
        if self.status != "PASS":
            raise AuditBlockedError("blocking audit issues prevent database construction")
        return AuditedBatch(self.records)


@dataclass(frozen=True)
class AuditContract:
    profile: AuditProfile
    release_version: str
    schema_version: str
    expected_question_count: int
    expected_source_count: int
    expected_answer_status_counts: tuple[tuple[str, int], ...]
    allowed_tags: tuple[str, ...]
    required_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.profile) is not str or self.profile not in {"V1.17", "V1.18"}:
            raise PipelineError("audit profile must be V1.17 or V1.18")
        object.__setattr__(
            self,
            "expected_answer_status_counts",
            _tuple_of_tuples(self.expected_answer_status_counts),
        )
        object.__setattr__(self, "allowed_tags", tuple(self.allowed_tags))
        object.__setattr__(self, "required_fields", tuple(self.required_fields))


@dataclass(frozen=True)
class AuditRequest:
    source_path: Path
    asset_root: Path
    contract: AuditContract
    selected_source_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_path", self.source_path.resolve())
        object.__setattr__(self, "asset_root", self.asset_root.resolve())
        object.__setattr__(self, "selected_source_ids", tuple(self.selected_source_ids))


@dataclass(frozen=True)
class DatabaseContract:
    profile: str
    expected_user_version: int
    expected_question_count: int
    expected_existing_question_count: int
    expected_new_question_count: int
    expected_answer_status_counts: tuple[tuple[str, int], ...]
    required_tables: tuple[str, ...]
    required_views: tuple[str, ...]
    journal_mode: str
    vacuum: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "expected_answer_status_counts",
            _tuple_of_tuples(self.expected_answer_status_counts),
        )
        object.__setattr__(self, "required_tables", tuple(self.required_tables))
        object.__setattr__(self, "required_views", tuple(self.required_views))


@dataclass(frozen=True)
class DatabaseBuildRequest:
    batch: AuditedBatch
    baseline_database: ArtifactRef
    baseline_manifest: ArtifactRef
    output_path: Path
    release_spec: ReleaseSpec
    contract: DatabaseContract

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_path", self.output_path.resolve())


@dataclass(frozen=True)
class VerificationCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class VerificationReport:
    status: str
    checks: tuple[VerificationCheck, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", tuple(self.checks))


@dataclass(frozen=True)
class DatabaseArtifact:
    database: ArtifactRef
    release_spec: ReleaseSpec
    verification_report: VerificationReport


@dataclass(frozen=True)
class ExportContract:
    profile: str
    csv_filename: str
    knowledge_markdown_filename: str
    import_report_filename: str
    project_state_filename: str
    taxonomy_filename: str | None
    expected_question_count: int
    expected_missing_answer_count: int


@dataclass(frozen=True)
class ExportRequest:
    database: DatabaseArtifact
    output_dir: Path
    contract: ExportContract

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_dir", self.output_dir.resolve())


@dataclass(frozen=True)
class ExportVerificationRequest:
    database: DatabaseArtifact
    artifacts: DerivedArtifacts
    contract: ExportContract


@dataclass(frozen=True)
class DerivedArtifacts:
    csv: ArtifactRef
    knowledge_markdown: ArtifactRef
    import_report: ArtifactRef
    project_state: ArtifactRef
    taxonomy: ArtifactRef | None


@dataclass(frozen=True)
class ReleaseContract:
    profile: str
    audit_records_filename: str
    audit_report_filename: str
    approval_filename: str
    manifest_filename: str
    sha256sums_filename: str
    candidate_zip_filename: str
    formal_zip_filename: str
    archive_root: str
    protected_artifact_kinds: tuple[str, ...]
    manifest_required_fields: tuple[str, ...]
    hash_excluded_kinds: tuple[str, ...]
    zip_excluded_kinds: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "protected_artifact_kinds",
            tuple(self.protected_artifact_kinds),
        )
        object.__setattr__(
            self,
            "manifest_required_fields",
            tuple(self.manifest_required_fields),
        )
        object.__setattr__(self, "hash_excluded_kinds", tuple(self.hash_excluded_kinds))
        object.__setattr__(self, "zip_excluded_kinds", tuple(self.zip_excluded_kinds))


@dataclass(frozen=True)
class CandidateBuildRequest:
    config: _config.PipelineConfig
    run_id: str
    release_spec: ReleaseSpec
    audit_request: AuditRequest
    database_contract: DatabaseContract
    export_contract: ExportContract
    release_contract: ReleaseContract


@dataclass(frozen=True)
class CandidateRelease:
    run_id: str
    release_version: str
    candidate_manifest_sha256: str
    verification_report: VerificationReport
    artifacts: tuple[ArtifactRef, ...]
    candidate_zip: ArtifactRef

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifacts", tuple(self.artifacts))


@dataclass(frozen=True)
class FormalRelease:
    release_dir: Path
    manifest: ArtifactRef
    verification_report: VerificationReport
    final_hashes: tuple[ArtifactRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_dir", self.release_dir.resolve())
        object.__setattr__(self, "final_hashes", tuple(self.final_hashes))
