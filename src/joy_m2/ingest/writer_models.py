"""Immutable public contracts for the Task 9C V1.19 candidate writer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from joy_m2.errors import ImportApprovalError as _ImportApprovalError
from joy_m2.errors import PipelineError
from joy_m2.ingest.models import ImportPreflightResult
from joy_m2.models import ArtifactRef, VerificationReport


_SHA256 = re.compile(r"[0-9a-f]{64}")
_BASELINE_TABLES = (
    "complete_question_corrections_v2",
    "complete_question_tags_v2",
    "complete_question_taxonomy_v2",
    "complete_questions_v2",
    "import_runs_v2",
    "question_topics",
    "questions",
    "release_metadata_v2",
    "sources",
    "topics",
)
_CANDIDATE_TABLES = (
    "task9_import_batches_v1",
    "task9_import_candidates_v1",
    "task9_import_images_v1",
    "task9_import_taxonomy_v1",
)
_CANDIDATE_VIEWS = ("task9_candidate_questions_v1",)
_CONTRACT_VALUES = {
    "profile": "V1.19",
    "candidate_manifest_schema": "task9-v119-candidate-manifest-v1",
    "candidate_database_schema": "task9-v119-candidate-v1",
    "expected_user_version": 119,
    "database_filename": "Joy_M2_V1.19_candidate.sqlite3",
    "manifest_filename": "candidate_manifest.json",
    "sha256s_filename": "SHA256SUMS",
    "rollback_filename": "rollback.json",
    "image_root": "images/sha256",
}


def _exact_tuple(value: object, item_type: type, name: str):
    if type(value) not in {list, tuple}:
        raise PipelineError(f"{name} must be a list or tuple")
    result = tuple(value)
    if any(type(item) is not item_type for item in result):
        raise PipelineError(f"{name} contains an invalid value")
    return result


def _resolved_path(value: object, name: str) -> Path:
    if not isinstance(value, Path):
        raise PipelineError(f"{name} must be a Path")
    return value.resolve(strict=False)


def _require_exact_carrier(value: object, expected: type, name: str) -> None:
    if type(value) is not expected:
        raise PipelineError(f"{name} must be an exact {expected.__name__}")


@dataclass(frozen=True)
class ImportApproval:
    batch_id: str
    preflight_sha256: str
    target_release_version: str
    statement: str

    def __post_init__(self) -> None:
        if type(self.batch_id) is not str or not self.batch_id:
            raise _ImportApprovalError("batch_id must be a non-empty string")
        if "\r" in self.batch_id or "\n" in self.batch_id:
            raise _ImportApprovalError("batch_id cannot contain CR or LF")
        if (
            type(self.preflight_sha256) is not str
            or _SHA256.fullmatch(self.preflight_sha256) is None
        ):
            raise _ImportApprovalError(
                "preflight_sha256 must be a lowercase SHA-256 digest"
            )
        if type(self.target_release_version) is not str or self.target_release_version != "V1.19":
            raise _ImportApprovalError("target_release_version must equal V1.19")
        expected = (
            f"USER APPROVED IMPORT BATCH {self.batch_id} "
            f"{self.preflight_sha256} V1.19"
        )
        if type(self.statement) is not str or self.statement != expected:
            raise _ImportApprovalError("statement must exactly bind the approved import")


@dataclass(frozen=True)
class V119WriterContract:
    profile: str
    candidate_manifest_schema: str
    candidate_database_schema: str
    expected_user_version: int
    database_filename: str
    manifest_filename: str
    sha256s_filename: str
    rollback_filename: str
    image_root: str
    required_baseline_tables: tuple[str, ...]
    required_candidate_tables: tuple[str, ...]
    required_candidate_views: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, expected in _CONTRACT_VALUES.items():
            value = getattr(self, name)
            if type(value) is not type(expected) or value != expected:
                raise PipelineError(f"{name} does not match the V1.19 writer contract")
        declared = (
            ("required_baseline_tables", self.required_baseline_tables, _BASELINE_TABLES),
            ("required_candidate_tables", self.required_candidate_tables, _CANDIDATE_TABLES),
            ("required_candidate_views", self.required_candidate_views, _CANDIDATE_VIEWS),
        )
        for name, value, expected in declared:
            normalized = _exact_tuple(value, str, name)
            if normalized != expected:
                raise PipelineError(f"{name} does not match the V1.19 writer contract")
            object.__setattr__(self, name, normalized)


@dataclass(frozen=True)
class V119WriteRequest:
    preflight_result: ImportPreflightResult
    package_root: Path
    approval: ImportApproval
    output_dir: Path
    contract: V119WriterContract

    def __post_init__(self) -> None:
        _require_exact_carrier(
            self.preflight_result, ImportPreflightResult, "preflight_result"
        )
        _require_exact_carrier(self.approval, ImportApproval, "approval")
        _require_exact_carrier(self.contract, V119WriterContract, "contract")
        object.__setattr__(
            self, "package_root", _resolved_path(self.package_root, "package_root")
        )
        object.__setattr__(
            self, "output_dir", _resolved_path(self.output_dir, "output_dir")
        )


@dataclass(frozen=True)
class V119VerificationRequest:
    candidate_dir: Path
    preflight_result: ImportPreflightResult
    approval: ImportApproval
    contract: V119WriterContract

    def __post_init__(self) -> None:
        _require_exact_carrier(
            self.preflight_result, ImportPreflightResult, "preflight_result"
        )
        _require_exact_carrier(self.approval, ImportApproval, "approval")
        _require_exact_carrier(self.contract, V119WriterContract, "contract")
        object.__setattr__(
            self, "candidate_dir", _resolved_path(self.candidate_dir, "candidate_dir")
        )


@dataclass(frozen=True)
class V119CandidateArtifacts:
    database: ArtifactRef
    manifest: ArtifactRef
    sha256sums: ArtifactRef
    rollback: ArtifactRef
    images: tuple[ArtifactRef, ...]
    verification_report: VerificationReport

    def __post_init__(self) -> None:
        artifacts = (
            ("database", self.database, "sqlite"),
            ("manifest", self.manifest, "manifest"),
            ("sha256sums", self.sha256sums, "sha256sums"),
            ("rollback", self.rollback, "rollback"),
        )
        for name, artifact, kind in artifacts:
            _require_exact_carrier(artifact, ArtifactRef, name)
            if artifact.kind != kind:
                raise PipelineError(f"{name} must have kind {kind}")
        images = _exact_tuple(self.images, ArtifactRef, "images")
        if any(image.kind != "image" for image in images):
            raise PipelineError("images must have kind image")
        if images != tuple(sorted(images, key=lambda image: image.path.as_posix())):
            raise PipelineError("images must be ordered by destination path")
        _require_exact_carrier(
            self.verification_report, VerificationReport, "verification_report"
        )
        object.__setattr__(self, "images", images)
