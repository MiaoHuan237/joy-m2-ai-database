"""Immutable public contracts for V1.22 formal promotion readiness."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from joy_m2.errors import PipelineError, PromotionError
from joy_m2.ingest.v122_models import V122CandidateVerificationRequest
from joy_m2.models import ArtifactRef, VerificationReport


_SHA256 = re.compile(r"[0-9a-f]{64}")
_CONTRACT_VALUES = {
    "profile": "V1.22",
    "release_manifest_schema": "task12-v122-formal-manifest-v1",
    "formal_database_schema": "task12-v122-formal-v1",
    "promotion_identity_schema": "task12-v122-promotion-identity-v1",
    "rollback_schema": "task12-v122-formal-rollback-v1",
    "expected_user_version": 122,
    "database_filename": "Joy_M2_Complete_Question_DB_V1_22.sqlite3",
    "manifest_filename": "manifest.json",
    "sha256s_filename": "SHA256SUMS.txt",
    "rollback_filename": "rollback.json",
    "image_root": "images/sha256",
    "promoted_table": "task12_v122_promoted_questions_v1",
    "promotion_table": "task12_v122_promotion_v1",
    "formal_view": "formal_complete_questions_v122",
}


def _exact(value: object, expected: type, name: str) -> None:
    if type(value) is not expected:
        raise PipelineError(f"{name} must be an exact {expected.__name__}")


def _path(value: object, name: str, *, resolve: bool) -> Path:
    if not isinstance(value, Path):
        raise PipelineError(f"{name} must be a Path")
    return value.resolve(strict=False) if resolve else value.absolute()


def _digest(value: object, name: str) -> None:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise PipelineError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class V122PromotionContract:
    profile: str
    release_manifest_schema: str
    formal_database_schema: str
    promotion_identity_schema: str
    rollback_schema: str
    expected_user_version: int
    database_filename: str
    manifest_filename: str
    sha256s_filename: str
    rollback_filename: str
    image_root: str
    promoted_table: str
    promotion_table: str
    formal_view: str

    def __post_init__(self) -> None:
        for name, expected in _CONTRACT_VALUES.items():
            value = getattr(self, name)
            if type(value) is not type(expected) or value != expected:
                raise PipelineError(f"{name} does not match the V1.22 promotion contract")


@dataclass(frozen=True)
class V122PromotionBuildRequest:
    candidate: V122CandidateVerificationRequest
    output_dir: Path
    contract: V122PromotionContract

    def __post_init__(self) -> None:
        _exact(self.candidate, V122CandidateVerificationRequest, "candidate")
        _exact(self.contract, V122PromotionContract, "contract")
        object.__setattr__(self, "output_dir", _path(self.output_dir, "output_dir", resolve=False))


@dataclass(frozen=True)
class V122PromotionVerificationRequest:
    release_dir: Path
    candidate: V122CandidateVerificationRequest
    contract: V122PromotionContract

    def __post_init__(self) -> None:
        _exact(self.candidate, V122CandidateVerificationRequest, "candidate")
        _exact(self.contract, V122PromotionContract, "contract")
        object.__setattr__(self, "release_dir", _path(self.release_dir, "release_dir", resolve=False))


@dataclass(frozen=True)
class V122ReleasePromotionApproval:
    release_version: str
    release_digest: str
    statement: str

    def __post_init__(self) -> None:
        if type(self.release_version) is not str or self.release_version != "V1.22":
            raise PromotionError("release_version must equal V1.22")
        if type(self.release_digest) is not str or _SHA256.fullmatch(self.release_digest) is None:
            raise PromotionError("release_digest must be a lowercase SHA-256 digest")
        expected = f"USER APPROVED RELEASE PROMOTION V1.22 {self.release_digest}"
        if type(self.statement) is not str or self.statement != expected:
            raise PromotionError("statement must exactly bind the V1.22 promotion")


@dataclass(frozen=True)
class V122PublicationRequest:
    dry_run_dir: Path
    candidate: V122CandidateVerificationRequest
    approval: V122ReleasePromotionApproval
    contract: V122PromotionContract

    def __post_init__(self) -> None:
        _exact(self.candidate, V122CandidateVerificationRequest, "candidate")
        _exact(self.approval, V122ReleasePromotionApproval, "approval")
        _exact(self.contract, V122PromotionContract, "contract")
        object.__setattr__(self, "dry_run_dir", _path(self.dry_run_dir, "dry_run_dir", resolve=False))


@dataclass(frozen=True)
class V122PromotionArtifacts:
    database: ArtifactRef
    manifest: ArtifactRef
    sha256sums: ArtifactRef
    rollback: ArtifactRef
    images: tuple[ArtifactRef, ...]
    release_digest: str
    verification_report: VerificationReport

    def __post_init__(self) -> None:
        for name, kind in (
            ("database", "sqlite"),
            ("manifest", "manifest"),
            ("sha256sums", "sha256sums"),
            ("rollback", "rollback"),
        ):
            value = getattr(self, name)
            _exact(value, ArtifactRef, name)
            if value.kind != kind:
                raise PipelineError(f"{name} must have kind {kind}")
        if type(self.images) not in {list, tuple}:
            raise PipelineError("images must be a list or tuple")
        images = tuple(self.images)
        if any(type(item) is not ArtifactRef or item.kind != "image" for item in images):
            raise PipelineError("images must contain exact image ArtifactRefs")
        if images != tuple(sorted(images, key=lambda item: item.path.as_posix())):
            raise PipelineError("images must be ordered by destination path")
        _digest(self.release_digest, "release_digest")
        _exact(self.verification_report, VerificationReport, "verification_report")
        object.__setattr__(self, "images", images)
