"""Immutable public authority models for Task 10A V1.22 candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from joy_m2.errors import ImportApprovalError, PipelineError
from joy_m2.ingest.models import (
    ImportAdaptation,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
)
from joy_m2.models import ArtifactRef, VerificationReport


_SHA256 = re.compile(r"[0-9a-f]{64}")
_BATCH_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_GENESIS_DIGEST = "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7"
_BASELINE = {
    "release_version": "V1.21",
    "question_count": 591,
    "database_sha256": "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a",
    "database_size_bytes": 10063872,
    "manifest_sha256": "a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40",
    "manifest_size_bytes": 7913,
    "release_digest": "f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3",
}
_MANIFEST_VALUES = {
    "schema_version": "task12-v122-import-manifest-v1",
    "project": "Joy M2 AI Database",
    "module": "M2",
    "target_release_version": "V1.22",
    "language_policy": "preserve_source_and_store_reviewed_chinese_separately",
    "split_policy": "one_complete_question_per_record",
    "difficulty_policy": "joy_level_1_5",
    "tag_policy": "controlled_primary_type_and_tags",
    "answer_policy": "preserve_source_answer_identity",
    "explanation_policy": "source_or_independently_verified_with_identity",
}
_CONTRACT_VALUES = {
    "profile": "V1.22",
    "baseline_release_version": _BASELINE["release_version"],
    "baseline_question_count": _BASELINE["question_count"],
    "baseline_database_sha256": _BASELINE["database_sha256"],
    "baseline_database_size_bytes": _BASELINE["database_size_bytes"],
    "baseline_manifest_sha256": _BASELINE["manifest_sha256"],
    "baseline_manifest_size_bytes": _BASELINE["manifest_size_bytes"],
    "baseline_release_digest": _BASELINE["release_digest"],
    "canonical_manifest_schema": _MANIFEST_VALUES["schema_version"],
    "preflight_schema": "task12-v122-preflight-v1",
    "approval_schema": "task12-v122-import-approval-v1",
    "candidate_manifest_schema": "task12-v122-candidate-manifest-v1",
    "candidate_database_schema": "task12-v122-candidate-v1",
    "candidate_identity_schema": "task12-v122-candidate-identity-v1",
    "rollback_schema": "task12-v122-rollback-v1",
    "expected_user_version": 122,
    "database_filename": "Joy_M2_V1.22_candidate.sqlite3",
    "manifest_filename": "candidate_manifest.json",
    "sha256s_filename": "SHA256SUMS",
    "rollback_filename": "rollback.json",
    "authority_root": "authority/batches",
    "image_root": "images/sha256",
    "required_baseline_view": "formal_complete_questions_v121",
}
_CANDIDATE_TABLES = (
    "task12_v122_batch_ledger_v1",
    "task12_v122_candidates_v1",
    "task12_v122_images_v1",
    "task12_v122_taxonomy_v1",
)
_CANDIDATE_VIEWS = ("task12_candidate_questions_v122",)
_REPORT_STATUSES = {
    "READY FOR USER IMPORT APPROVAL",
    "BLOCKED — IMPORT PREFLIGHT FAILED",
}


def _require_str(value: object, name: str, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        raise PipelineError(f"{name} must be a{' non-empty' if nonempty else ''} string")
    return value


def _require_sha(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise PipelineError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _require_batch_id(value: object, name: str = "batch_id") -> str:
    if type(value) is not str or _BATCH_ID.fullmatch(value) is None:
        raise PipelineError(f"{name} must be a canonical V1.22 batch identifier")
    return value


def _exact_tuple(value: object, item_type: type, name: str, *, nonempty: bool = False) -> tuple:
    if type(value) not in {list, tuple}:
        raise PipelineError(f"{name} must be a list or tuple")
    result = tuple(value)
    if (nonempty and not result) or any(type(item) is not item_type for item in result):
        raise PipelineError(f"{name} contains an invalid value")
    return result


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if type(value) not in {list, tuple}:
        raise PipelineError(f"{name} must be a list or tuple")
    result = tuple(value)
    if any(type(item) is not str or not item for item in result):
        raise PipelineError(f"{name} contains an invalid string")
    return result


def _path(value: object, name: str) -> Path:
    if not isinstance(value, Path):
        raise PipelineError(f"{name} must be a Path")
    return value.resolve(strict=False)


def _lexical_path(value: object, name: str) -> Path:
    if not isinstance(value, Path):
        raise PipelineError(f"{name} must be a Path")
    return value.absolute()


def _artifact(value: object, name: str, kind: str | None = None) -> ArtifactRef:
    if type(value) is not ArtifactRef:
        raise PipelineError(f"{name} must be an exact ArtifactRef")
    _require_sha(value.sha256, f"{name}.sha256")
    if type(value.size_bytes) is not int or value.size_bytes < 0:
        raise PipelineError(f"{name}.size_bytes must be a non-negative integer")
    if kind is not None and value.kind != kind:
        raise PipelineError(f"{name} must have kind {kind}")
    return value


def _baseline_artifact(value: object, name: str) -> ArtifactRef:
    artifact = _artifact(value, name, "sqlite")
    if (
        type(artifact.sha256) is not str
        or artifact.sha256 != _BASELINE["database_sha256"]
        or type(artifact.size_bytes) is not int
        or artifact.size_bytes != _BASELINE["database_size_bytes"]
    ):
        raise PipelineError(f"{name} does not match the V1.21 baseline authority")
    return artifact


def _validate_report_tuples(report: "V122ImportPreflightReport") -> None:
    for name in (
        "readable_files", "unreadable_files", "unsupported_files", "ambiguous_splits",
        "missing_answers", "missing_explanations", "incomplete_enrichments",
        "missing_images", "orphan_images", "proposed_ids", "warnings", "blocking_errors",
    ):
        object.__setattr__(report, name, _string_tuple(getattr(report, name), name))
    adaptations = _exact_tuple(report.adaptations, ImportAdaptation, "adaptations")
    object.__setattr__(
        report,
        "adaptations",
        tuple(sorted(adaptations, key=lambda item: (
            item.candidate_id, item.reference_question_id, item.adaptation_kind,
            item.evidence, item.reason,
        ))),
    )
    if type(report.level_counts) not in {list, tuple}:
        raise PipelineError("level_counts must be a list or tuple")
    levels = tuple(tuple(item) for item in report.level_counts)
    if any(
        len(item) != 2 or type(item[0]) is not int or type(item[1]) is not int
        or not 1 <= item[0] <= 5 or item[1] < 0
        for item in levels
    ):
        raise PipelineError("level_counts is invalid")
    if tuple(level for level, _ in levels) != tuple(sorted(level for level, _ in levels)):
        raise PipelineError("level_counts must be sorted")
    object.__setattr__(report, "level_counts", levels)


@dataclass(frozen=True)
class V122BatchImportManifest:
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
        _require_batch_id(self.batch_id)
        _require_str(self.chapter, "chapter")
        for name, expected in _MANIFEST_VALUES.items():
            value = getattr(self, name)
            if type(value) is not str or value != expected:
                raise PipelineError(f"{name} must be exactly {expected!r}")
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
class V122AdaptedImportPackage:
    package_root: Path
    manifest_path: Path
    manifest: V122BatchImportManifest

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_root", _path(self.package_root, "package_root"))
        object.__setattr__(self, "manifest_path", _path(self.manifest_path, "manifest_path"))
        if type(self.manifest) is not V122BatchImportManifest:
            raise PipelineError("manifest must be an exact V122BatchImportManifest")


@dataclass(frozen=True)
class V122ImportApproval:
    batch_id: str
    preflight_sha256: str
    target_release_version: str
    parent_candidate_digest: str
    statement: str

    def __post_init__(self) -> None:
        try:
            _require_batch_id(self.batch_id)
            _require_sha(self.preflight_sha256, "preflight_sha256")
            _require_sha(self.parent_candidate_digest, "parent_candidate_digest")
        except PipelineError as error:
            raise ImportApprovalError(str(error)) from error
        if type(self.target_release_version) is not str or self.target_release_version != "V1.22":
            raise ImportApprovalError("target_release_version must equal V1.22")
        expected = (
            f"USER APPROVED IMPORT BATCH {self.batch_id} {self.preflight_sha256} "
            f"V1.22 PARENT {self.parent_candidate_digest}"
        )
        if type(self.statement) is not str or self.statement != expected:
            raise ImportApprovalError("statement must exactly bind the approved import batch")


@dataclass(frozen=True)
class V122BatchLedgerEntry:
    ordinal: int
    batch_id: str
    parent_candidate_digest: str
    preflight_sha256: str
    manifest_sha256: str
    approval: V122ImportApproval
    batch_candidate_count: int
    cumulative_candidate_count: int
    projected_question_count: int

    def __post_init__(self) -> None:
        if type(self.ordinal) is not int or self.ordinal < 1:
            raise PipelineError("ordinal must be a positive integer")
        _require_batch_id(self.batch_id)
        for name in ("parent_candidate_digest", "preflight_sha256", "manifest_sha256"):
            _require_sha(getattr(self, name), name)
        if self.ordinal == 1 and self.parent_candidate_digest != _GENESIS_DIGEST:
            raise PipelineError("the first ledger entry must bind the fixed genesis digest")
        if type(self.approval) is not V122ImportApproval:
            raise PipelineError("approval must be an exact V122ImportApproval")
        if (
            self.approval.batch_id != self.batch_id
            or self.approval.preflight_sha256 != self.preflight_sha256
            or self.approval.target_release_version != "V1.22"
            or self.approval.parent_candidate_digest != self.parent_candidate_digest
        ):
            raise PipelineError("approval does not bind this ledger entry")
        for name in ("batch_candidate_count", "cumulative_candidate_count", "projected_question_count"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise PipelineError(f"{name} must be a non-negative integer")
        if self.cumulative_candidate_count < self.batch_candidate_count:
            raise PipelineError("cumulative candidate count cannot precede batch count")
        if self.projected_question_count != 591 + self.cumulative_candidate_count:
            raise PipelineError("projected question count does not close")


@dataclass(frozen=True)
class V122EffectiveState:
    baseline_database: ArtifactRef
    candidate_digest: str
    batch_ledger: tuple[V122BatchLedgerEntry, ...]
    candidate_count: int
    projected_question_count: int

    def __post_init__(self) -> None:
        _baseline_artifact(self.baseline_database, "baseline_database")
        _require_sha(self.candidate_digest, "candidate_digest")
        ledger = _exact_tuple(self.batch_ledger, V122BatchLedgerEntry, "batch_ledger")
        if type(self.candidate_count) is not int or self.candidate_count < 0:
            raise PipelineError("candidate_count must be a non-negative integer")
        if type(self.projected_question_count) is not int or self.projected_question_count < 0:
            raise PipelineError("projected_question_count must be a non-negative integer")
        if not ledger:
            if (
                self.candidate_digest != _GENESIS_DIGEST
                or self.candidate_count != 0
                or self.projected_question_count != 591
            ):
                raise PipelineError("empty V1.22 state must be the fixed genesis state")
        else:
            previous_count = 0
            batch_ids: set[str] = set()
            preflights: set[str] = set()
            for expected_ordinal, entry in enumerate(ledger, start=1):
                if entry.ordinal != expected_ordinal:
                    raise PipelineError("batch ledger ordinals must be contiguous")
                if entry.batch_id in batch_ids or entry.preflight_sha256 in preflights:
                    raise PipelineError("batch ledger identities must be unique")
                if entry.cumulative_candidate_count != previous_count + entry.batch_candidate_count:
                    raise PipelineError("batch ledger cumulative counts must be contiguous")
                previous_count = entry.cumulative_candidate_count
                batch_ids.add(entry.batch_id)
                preflights.add(entry.preflight_sha256)
            if self.candidate_count != ledger[-1].cumulative_candidate_count:
                raise PipelineError("candidate_count does not match ledger closure")
            if self.projected_question_count != ledger[-1].projected_question_count:
                raise PipelineError("projected_question_count does not match ledger closure")
        if self.projected_question_count != 591 + self.candidate_count:
            raise PipelineError("effective state count does not close")
        object.__setattr__(self, "batch_ledger", ledger)


@dataclass(frozen=True)
class V122CandidateContract:
    profile: str
    baseline_release_version: str
    baseline_question_count: int
    baseline_database_sha256: str
    baseline_database_size_bytes: int
    baseline_manifest_sha256: str
    baseline_manifest_size_bytes: int
    baseline_release_digest: str
    canonical_manifest_schema: str
    preflight_schema: str
    approval_schema: str
    candidate_manifest_schema: str
    candidate_database_schema: str
    candidate_identity_schema: str
    rollback_schema: str
    expected_user_version: int
    database_filename: str
    manifest_filename: str
    sha256s_filename: str
    rollback_filename: str
    authority_root: str
    image_root: str
    required_baseline_view: str
    required_candidate_tables: tuple[str, ...]
    required_candidate_views: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, expected in _CONTRACT_VALUES.items():
            value = getattr(self, name)
            if type(value) is not type(expected) or value != expected:
                raise PipelineError(f"{name} does not match the V1.22 candidate contract")
        tables = _exact_tuple(self.required_candidate_tables, str, "required_candidate_tables")
        views = _exact_tuple(self.required_candidate_views, str, "required_candidate_views")
        if tables != _CANDIDATE_TABLES or views != _CANDIDATE_VIEWS:
            raise PipelineError("candidate contract object tuples do not match V1.22")
        object.__setattr__(self, "required_candidate_tables", tables)
        object.__setattr__(self, "required_candidate_views", views)


@dataclass(frozen=True)
class V122PreflightRequest:
    manifest: V122BatchImportManifest
    package_root: Path
    baseline_database: ArtifactRef
    parent_candidate: V122CandidateVerificationRequest | None
    contract: V122CandidateContract

    def __post_init__(self) -> None:
        if type(self.manifest) is not V122BatchImportManifest:
            raise PipelineError("manifest must be an exact V122BatchImportManifest")
        object.__setattr__(self, "package_root", _path(self.package_root, "package_root"))
        _baseline_artifact(self.baseline_database, "baseline_database")
        if self.parent_candidate is not None and type(self.parent_candidate) is not V122CandidateVerificationRequest:
            raise PipelineError("parent_candidate must be V122CandidateVerificationRequest or None")
        if type(self.contract) is not V122CandidateContract:
            raise PipelineError("contract must be an exact V122CandidateContract")


@dataclass(frozen=True)
class V122ImportPreflightReport:
    batch_id: str
    status: str
    preflight_sha256: str
    manifest_sha256: str
    baseline_version: str
    baseline_release_digest: str
    baseline_question_count: int
    target_release_version: str
    parent_candidate_digest: str
    parent_batch_count: int
    before_count: int
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
        _require_batch_id(self.batch_id)
        _require_sha(self.preflight_sha256, "preflight_sha256")
        _require_sha(self.manifest_sha256, "manifest_sha256")
        _require_sha(self.parent_candidate_digest, "parent_candidate_digest")
        if (
            type(self.baseline_version) is not str or self.baseline_version != _BASELINE["release_version"]
            or type(self.baseline_release_digest) is not str or self.baseline_release_digest != _BASELINE["release_digest"]
            or type(self.baseline_question_count) is not int or self.baseline_question_count != 591
            or type(self.target_release_version) is not str or self.target_release_version != "V1.22"
        ):
            raise PipelineError("preflight report baseline or target identity is invalid")
        if type(self.status) is not str or self.status not in _REPORT_STATUSES:
            raise PipelineError("preflight report status is invalid")
        count_names = (
            "parent_batch_count", "before_count", "detected_count", "new_candidate_count",
            "duplicate_count", "rejected_count", "ambiguous_count", "approved_count",
            "projected_after_count", "teacher_notes_file_count", "common_errors_file_count",
        )
        for name in count_names:
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise PipelineError(f"{name} must be a non-negative integer")
        if self.before_count < 591:
            raise PipelineError("before_count cannot precede the V1.21 baseline")
        if self.detected_count != self.new_candidate_count + self.duplicate_count + self.rejected_count:
            raise PipelineError("detected count does not close")
        if self.projected_after_count != self.before_count + self.new_candidate_count:
            raise PipelineError("projected count does not close")
        if self.approved_count != 0 or self.ambiguous_count > self.rejected_count:
            raise PipelineError("preflight approval or ambiguity count is invalid")
        _validate_report_tuples(self)


@dataclass(frozen=True)
class V122ImportPreflightResult:
    manifest: V122BatchImportManifest
    effective_state: V122EffectiveState
    candidates: tuple[ImportCandidate, ...]
    issues: tuple[ImportIssue, ...]
    report: V122ImportPreflightReport

    def __post_init__(self) -> None:
        if type(self.manifest) is not V122BatchImportManifest:
            raise PipelineError("manifest must be an exact V122BatchImportManifest")
        if type(self.effective_state) is not V122EffectiveState:
            raise PipelineError("effective_state must be an exact V122EffectiveState")
        if type(self.report) is not V122ImportPreflightReport:
            raise PipelineError("report must be an exact V122ImportPreflightReport")
        if (
            self.report.batch_id != self.manifest.batch_id
            or self.report.parent_candidate_digest != self.effective_state.candidate_digest
            or self.report.parent_batch_count != len(self.effective_state.batch_ledger)
            or self.report.before_count != self.effective_state.projected_question_count
        ):
            raise PipelineError("preflight result does not bind its effective state")
        object.__setattr__(self, "candidates", _exact_tuple(self.candidates, ImportCandidate, "candidates"))
        issues = _exact_tuple(self.issues, ImportIssue, "issues")
        object.__setattr__(
            self,
            "issues",
            tuple(sorted(issues, key=lambda issue: (
                issue.proposed_question_id or "", issue.code, issue.field, issue.evidence,
            ))),
        )


@dataclass(frozen=True)
class V122ApprovedBatch:
    preflight_result: V122ImportPreflightResult
    package_root: Path
    approval: V122ImportApproval

    def __post_init__(self) -> None:
        if type(self.preflight_result) is not V122ImportPreflightResult:
            raise PipelineError("preflight_result must be an exact V122ImportPreflightResult")
        object.__setattr__(self, "package_root", _path(self.package_root, "package_root"))
        if type(self.approval) is not V122ImportApproval:
            raise PipelineError("approval must be an exact V122ImportApproval")
        report = self.preflight_result.report
        if report.status != "READY FOR USER IMPORT APPROVAL" or report.blocking_errors:
            raise ImportApprovalError("only a ready preflight without blockers may be approved")
        if (
            self.approval.batch_id != self.preflight_result.manifest.batch_id
            or self.approval.preflight_sha256 != report.preflight_sha256
            or self.approval.target_release_version != report.target_release_version
            or self.approval.parent_candidate_digest != report.parent_candidate_digest
        ):
            raise ImportApprovalError("approval does not bind the exact ready preflight")


@dataclass(frozen=True)
class V122CandidateBuildRequest:
    approved_batches: tuple[V122ApprovedBatch, ...]
    output_dir: Path
    contract: V122CandidateContract

    def __post_init__(self) -> None:
        object.__setattr__(self, "approved_batches", _exact_tuple(
            self.approved_batches, V122ApprovedBatch, "approved_batches", nonempty=True,
        ))
        object.__setattr__(self, "output_dir", _lexical_path(self.output_dir, "output_dir"))
        if type(self.contract) is not V122CandidateContract:
            raise PipelineError("contract must be an exact V122CandidateContract")


@dataclass(frozen=True)
class V122CandidateVerificationRequest:
    candidate_dir: Path
    approved_batches: tuple[V122ApprovedBatch, ...]
    contract: V122CandidateContract

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_dir", _lexical_path(self.candidate_dir, "candidate_dir"))
        object.__setattr__(self, "approved_batches", _exact_tuple(
            self.approved_batches, V122ApprovedBatch, "approved_batches", nonempty=True,
        ))
        if type(self.contract) is not V122CandidateContract:
            raise PipelineError("contract must be an exact V122CandidateContract")


@dataclass(frozen=True)
class V122CandidateArtifacts:
    database: ArtifactRef
    manifest: ArtifactRef
    sha256sums: ArtifactRef
    rollback: ArtifactRef
    batch_authorities: tuple[ArtifactRef, ...]
    images: tuple[ArtifactRef, ...]
    state: V122EffectiveState
    verification_report: VerificationReport

    def __post_init__(self) -> None:
        for name, kind in (
            ("database", "sqlite"), ("manifest", "manifest"),
            ("sha256sums", "sha256sums"), ("rollback", "rollback"),
        ):
            _artifact(getattr(self, name), name, kind)
        authorities = _exact_tuple(self.batch_authorities, ArtifactRef, "batch_authorities")
        for authority in authorities:
            _artifact(authority, "batch_authority")
        if any(item.kind not in {"preflight", "approval"} for item in authorities):
            raise PipelineError("batch_authorities must contain preflight or approval artifacts")
        if authorities != tuple(sorted(authorities, key=lambda item: item.path.as_posix())):
            raise PipelineError("batch_authorities must be ordered by destination path")
        images = _exact_tuple(self.images, ArtifactRef, "images")
        for image in images:
            _artifact(image, "image")
        if any(item.kind != "image" for item in images):
            raise PipelineError("images must have kind image")
        if images != tuple(sorted(images, key=lambda item: item.path.as_posix())):
            raise PipelineError("images must be ordered by destination path")
        if type(self.state) is not V122EffectiveState:
            raise PipelineError("state must be an exact V122EffectiveState")
        if type(self.verification_report) is not VerificationReport:
            raise PipelineError("verification_report must be an exact VerificationReport")
        object.__setattr__(self, "batch_authorities", authorities)
        object.__setattr__(self, "images", images)
