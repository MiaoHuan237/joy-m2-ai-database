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


def _validated_counts(values, field_name: str) -> tuple[tuple[str, int], ...]:
    normalized = _tuple_of_tuples(values)
    declared: dict[str, int] = {}
    for entry in normalized:
        if len(entry) != 2:
            raise PipelineError(f"{field_name} entries must contain two values")
        name, count = entry
        if type(name) is not str:
            raise PipelineError(f"{field_name} names must be strings")
        if type(count) is not int or count <= 0:
            raise PipelineError(f"{field_name} counts must be positive integers")
        if name in declared:
            raise PipelineError(f"{field_name} classifications must be unique")
        declared[name] = count
    if tuple(declared) != tuple(sorted(declared)):
        raise PipelineError(f"{field_name} keys must be sorted")
    return normalized


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
class V117ReleaseDecision:
    formal_release_version: Literal["V1.17"]
    selectable: Literal[True]
    record_status: Literal["published"]
    joy_approval: Literal["approved_by_joy"]
    approved_at: Literal["2026-08-08T20:00:00+08:00"]
    schema_version: Literal["complete-question-v1.0"]

    def __post_init__(self) -> None:
        expected = (
            ("formal_release_version", str, "V1.17"),
            ("selectable", bool, True),
            ("record_status", str, "published"),
            ("joy_approval", str, "approved_by_joy"),
            ("approved_at", str, "2026-08-08T20:00:00+08:00"),
            ("schema_version", str, "complete-question-v1.0"),
        )
        for field_name, value_type, wanted in expected:
            value = getattr(self, field_name)
            if type(value) is not value_type or value != wanted:
                raise PipelineError(f"{field_name} must equal {wanted!r}")


@dataclass(frozen=True)
class V117ReleaseRecord:
    audited_record: AuditedRecord
    publication_evidence: PublicationEvidence
    release_compatibility: ReleaseCompatibility
    schema_version: str

    def __post_init__(self) -> None:
        if type(self.audited_record) is not AuditedRecord:
            raise PipelineError("audited_record must be an AuditedRecord")
        if (
            self.audited_record.task4_compatibility is None
            or self.audited_record.release_compatibility is not None
        ):
            raise PipelineError("audited_record must be a V1.17 audit envelope")
        audit_evidence = self.audited_record.question.publication_evidence
        if (
            audit_evidence.record_status != "audit_passed"
            or audit_evidence.joy_approval != ""
            or audit_evidence.approved_at is not None
            or self.audited_record.question.schema_version
            != "complete-question-v1.0-draft"
            or self.audited_record.question.unresolved_issues
        ):
            raise PipelineError("audited_record must retain V1.17 audit-stage values")
        if type(self.publication_evidence) is not PublicationEvidence:
            raise PipelineError("publication_evidence must be PublicationEvidence")
        if (
            self.publication_evidence.record_status != "published"
            or self.publication_evidence.joy_approval != "approved_by_joy"
            or self.publication_evidence.approved_at
            != "2026-08-08T20:00:00+08:00"
        ):
            raise PipelineError("publication_evidence must contain V1.17 release values")
        if type(self.release_compatibility) is not ReleaseCompatibility:
            raise PipelineError("release_compatibility must be ReleaseCompatibility")
        if (
            self.release_compatibility.formal_release_version != "V1.17"
            or self.release_compatibility.selectable is not True
            or self.release_compatibility.source_order <= 0
        ):
            raise PipelineError("release_compatibility must contain V1.17 release values")
        if type(self.schema_version) is not str or self.schema_version != "complete-question-v1.0":
            raise PipelineError("schema_version must equal 'complete-question-v1.0'")


@dataclass(frozen=True)
class V117ReleaseBatch:
    records: tuple[V117ReleaseRecord, ...]

    def __post_init__(self) -> None:
        if type(self.records) not in {list, tuple}:
            raise PipelineError("records must be a list or tuple of V117ReleaseRecord values")
        records = tuple(self.records)
        if any(type(record) is not V117ReleaseRecord for record in records):
            raise PipelineError("records must contain only V117ReleaseRecord values")
        if tuple(record.release_compatibility.source_order for record in records) != tuple(
            range(1, len(records) + 1)
        ):
            raise PipelineError("records must preserve contiguous one-based source_order")
        object.__setattr__(self, "records", records)


@dataclass(frozen=True)
class AuditInputEvidence:
    candidate_json: ArtifactRef
    baseline_database: ArtifactRef

    def __post_init__(self) -> None:
        if type(self.candidate_json) is not ArtifactRef:
            raise PipelineError("candidate_json must be an ArtifactRef")
        if type(self.baseline_database) is not ArtifactRef:
            raise PipelineError("baseline_database must be an ArtifactRef")


@dataclass(frozen=True)
class AuditReport:
    release_version: str
    status: str
    candidate_count: int
    source_count: int
    audit_passed: int
    audit_pending: int
    blocked: int
    exact_duplicate_count: int
    answer_status_counts: tuple[tuple[str, int], ...]
    image_reference_count: int
    source_counts: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        if type(self.release_version) is not str:
            raise PipelineError("audit report release_version must be a string")
        if self.status not in {"passed", "failed"}:
            raise PipelineError("audit report status must be 'passed' or 'failed'")
        for field_name in (
            "candidate_count",
            "source_count",
            "audit_passed",
            "audit_pending",
            "blocked",
            "exact_duplicate_count",
            "image_reference_count",
        ):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise PipelineError(f"audit report {field_name} must be a non-negative integer")
        answer_status_counts = _validated_counts(
            self.answer_status_counts,
            "answer_status_counts",
        )
        source_counts = _validated_counts(self.source_counts, "source_counts")
        object.__setattr__(self, "answer_status_counts", answer_status_counts)
        object.__setattr__(self, "source_counts", source_counts)

        if self.audit_pending != 0:
            raise PipelineError("audit_pending must be zero")
        if self.audit_passed + self.blocked != self.candidate_count:
            raise PipelineError("audit_passed and blocked must partition candidate_count")
        expected_status = "failed" if self.blocked else "passed"
        if self.status != expected_status:
            raise PipelineError("audit report status is inconsistent with blocked records")
        if self.exact_duplicate_count > self.blocked:
            raise PipelineError("exact_duplicate_count cannot exceed blocked")
        if sum(count for _, count in answer_status_counts) != self.candidate_count:
            raise PipelineError("answer_status_counts must cover every candidate record")
        if len(source_counts) != self.source_count:
            raise PipelineError("source_count must equal the number of distinct sources")
        if sum(count for _, count in source_counts) != self.candidate_count:
            raise PipelineError("source_counts must cover every candidate record")


@dataclass(frozen=True)
class AuditResult:
    records: tuple[AuditedRecord, ...]
    issues: tuple[AuditIssue, ...]
    answer_status_counts: tuple[tuple[str, int], ...]
    status: str
    report: AuditReport
    input_evidence: AuditInputEvidence

    def __post_init__(self) -> None:
        records = tuple(self.records)
        issues = tuple(self.issues)
        if any(type(record) is not AuditedRecord for record in records):
            raise PipelineError("records must contain only AuditedRecord values")
        if any(type(issue) is not AuditIssue for issue in issues):
            raise PipelineError("issues must contain only AuditIssue values")
        issues = tuple(
            sorted(
                issues,
                key=lambda issue: (
                    issue.question_id,
                    issue.code,
                    issue.field,
                    issue.evidence,
                ),
            )
        )
        answer_status_counts = _validated_counts(
            self.answer_status_counts,
            "answer_status_counts",
        )
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "issues", issues)
        object.__setattr__(self, "answer_status_counts", answer_status_counts)

        if type(self.report) is not AuditReport:
            raise PipelineError("report must be an AuditReport")
        if type(self.input_evidence) is not AuditInputEvidence:
            raise PipelineError("input_evidence must be AuditInputEvidence")

        expected_status = "failed" if issues else "passed"
        if self.status != expected_status:
            raise PipelineError(
                f"audit status {self.status!r} is inconsistent with issues"
            )
        if self.report.status != self.status:
            raise PipelineError("audit result and report status must be equal")

        actual_answer_counts = tuple(
            sorted(Counter(record.question.answer_status for record in records).items())
        )
        if answer_status_counts != actual_answer_counts:
            raise PipelineError(
                "answer_status_counts is inconsistent with audited records"
            )
        if self.report.answer_status_counts != answer_status_counts:
            raise PipelineError("result and report answer_status_counts must be equal")

        record_ids = {record.question.question_id for record in records}
        if any(issue.question_id not in record_ids for issue in issues):
            raise PipelineError("audit issues must refer to audited record ids")
        blocker_ids = {
            issue.question_id for issue in issues if issue.severity == "blocker"
        }
        exact_duplicate_ids = {
            issue.question_id
            for issue in issues
            if issue.severity == "blocker" and issue.code == "exact_duplicate"
        }
        actual_source_counts = tuple(
            sorted(Counter(record.question.source_id for record in records).items())
        )
        expected_report_values = {
            "candidate_count": len(records),
            "source_count": len(actual_source_counts),
            "audit_passed": len(records) - len(blocker_ids),
            "audit_pending": 0,
            "blocked": len(blocker_ids),
            "exact_duplicate_count": len(exact_duplicate_ids),
            "image_reference_count": sum(
                len(record.question.image_paths) for record in records
            ),
            "source_counts": actual_source_counts,
        }
        for field_name, expected in expected_report_values.items():
            if getattr(self.report, field_name) != expected:
                raise PipelineError(
                    f"audit report {field_name} is inconsistent with audited records"
                )

    def require_passed(self) -> AuditedBatch:
        if self.status != "passed":
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
    candidate_path: Path
    baseline_database: ArtifactRef
    asset_root: Path
    contract: AuditContract
    selected_source_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_path", self.candidate_path.resolve())
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
    batch: AuditedBatch | V117ReleaseBatch
    baseline_database: ArtifactRef
    baseline_manifest: ArtifactRef
    output_path: Path
    release_spec: ReleaseSpec
    contract: DatabaseContract

    def __post_init__(self) -> None:
        if type(self.batch) not in {AuditedBatch, V117ReleaseBatch}:
            raise PipelineError("batch must be AuditedBatch or V117ReleaseBatch")
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
    audit_records_filename: str
    audit_report_filename: str
    csv_filename: str
    knowledge_markdown_filename: str
    import_report_filename: str
    project_state_filename: str
    taxonomy_filename: str | None
    expected_question_count: int
    expected_missing_answer_count: int

    def __post_init__(self) -> None:
        if type(self.profile) is not str or self.profile not in {"V1.17", "V1.18"}:
            raise PipelineError("export profile must be V1.17 or V1.18")
        for field_name in (
            "audit_records_filename",
            "audit_report_filename",
            "csv_filename",
            "knowledge_markdown_filename",
            "import_report_filename",
            "project_state_filename",
        ):
            if type(getattr(self, field_name)) is not str:
                raise PipelineError(f"{field_name} must be a string")
        if self.taxonomy_filename is not None and type(self.taxonomy_filename) is not str:
            raise PipelineError("taxonomy_filename must be a string or None")
        for field_name in (
            "expected_question_count",
            "expected_missing_answer_count",
        ):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise PipelineError(f"{field_name} must be a non-negative integer")
        if self.expected_missing_answer_count > self.expected_question_count:
            raise PipelineError(
                "expected_missing_answer_count cannot exceed expected_question_count"
            )


@dataclass(frozen=True)
class ExportRequest:
    database: DatabaseArtifact
    audit_result: AuditResult
    record_batch: AuditedBatch | V117ReleaseBatch
    output_dir: Path
    contract: ExportContract

    def __post_init__(self) -> None:
        if type(self.database) is not DatabaseArtifact:
            raise PipelineError("database must be a DatabaseArtifact")
        if type(self.audit_result) is not AuditResult:
            raise PipelineError("audit_result must be an AuditResult")
        if type(self.record_batch) not in {AuditedBatch, V117ReleaseBatch}:
            raise PipelineError("record_batch must be AuditedBatch or V117ReleaseBatch")
        if not isinstance(self.output_dir, Path):
            raise PipelineError("output_dir must be a Path")
        if type(self.contract) is not ExportContract:
            raise PipelineError("contract must be an ExportContract")

        self.audit_result.require_passed()
        profile = self.contract.profile
        if self.database.release_spec.release_version != profile:
            raise PipelineError("database release version must match export profile")
        if self.audit_result.report.release_version != profile:
            raise PipelineError("audit report release version must match export profile")
        if profile == "V1.18":
            if type(self.record_batch) is not AuditedBatch:
                raise PipelineError("V1.18 export requires an AuditedBatch")
            batch_records = self.record_batch.records
        else:
            if type(self.record_batch) is not V117ReleaseBatch:
                raise PipelineError("V1.17 export requires a V117ReleaseBatch")
            batch_records = tuple(
                record.audited_record for record in self.record_batch.records
            )
        if batch_records != self.audit_result.records:
            raise PipelineError("record_batch must match audit_result records and order")
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
    audit_records: ArtifactRef
    audit_report: ArtifactRef

    def __post_init__(self) -> None:
        for field_name in (
            "csv",
            "knowledge_markdown",
            "import_report",
            "project_state",
            "audit_records",
            "audit_report",
        ):
            if type(getattr(self, field_name)) is not ArtifactRef:
                raise PipelineError(f"{field_name} must be an ArtifactRef")
        if self.taxonomy is not None and type(self.taxonomy) is not ArtifactRef:
            raise PipelineError("taxonomy must be an ArtifactRef or None")


@dataclass(frozen=True)
class ReleaseContract:
    profile: str
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
    v117_release_decision: V117ReleaseDecision | None
    baseline_manifest: ArtifactRef
    database_contract: DatabaseContract
    export_contract: ExportContract
    release_contract: ReleaseContract

    def __post_init__(self) -> None:
        expected_types = (
            ("config", _config.PipelineConfig),
            ("run_id", str),
            ("release_spec", ReleaseSpec),
            ("audit_request", AuditRequest),
            ("baseline_manifest", ArtifactRef),
            ("database_contract", DatabaseContract),
            ("export_contract", ExportContract),
            ("release_contract", ReleaseContract),
        )
        for field_name, value_type in expected_types:
            if type(getattr(self, field_name)) is not value_type:
                raise PipelineError(f"{field_name} must be a {value_type.__name__}")
        if self.release_spec.release_version not in {"V1.17", "V1.18"}:
            raise PipelineError("release_version must be V1.17 or V1.18")
        if self.release_spec.release_version == "V1.17":
            if type(self.v117_release_decision) is not V117ReleaseDecision:
                raise PipelineError(
                    "V1.17 requires an explicit V117ReleaseDecision"
                )
        elif self.v117_release_decision is not None:
            raise PipelineError("V1.18 requires v117_release_decision to be None")


@dataclass(frozen=True)
class CandidateRelease:
    run_id: str
    release_version: str
    release_contract: ReleaseContract
    candidate_manifest_sha256: str
    verification_report: VerificationReport
    artifacts: tuple[ArtifactRef, ...]
    candidate_zip: ArtifactRef

    def __post_init__(self) -> None:
        expected_types = (
            ("run_id", str),
            ("release_version", str),
            ("release_contract", ReleaseContract),
            ("candidate_manifest_sha256", str),
            ("verification_report", VerificationReport),
            ("candidate_zip", ArtifactRef),
        )
        for field_name, value_type in expected_types:
            if type(getattr(self, field_name)) is not value_type:
                raise PipelineError(f"{field_name} must be a {value_type.__name__}")
        if type(self.artifacts) not in {list, tuple}:
            raise PipelineError("artifacts must be a list or tuple of ArtifactRef values")
        artifacts = tuple(self.artifacts)
        if any(type(artifact) is not ArtifactRef for artifact in artifacts):
            raise PipelineError("artifacts must contain only ArtifactRef values")
        object.__setattr__(self, "artifacts", artifacts)


@dataclass(frozen=True)
class FormalRelease:
    release_dir: Path
    manifest: ArtifactRef
    verification_report: VerificationReport
    final_hashes: tuple[ArtifactRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_dir", self.release_dir.resolve())
        object.__setattr__(self, "final_hashes", tuple(self.final_hashes))
