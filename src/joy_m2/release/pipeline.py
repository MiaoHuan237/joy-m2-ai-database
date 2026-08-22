"""Atomic candidate construction, verification, and approval-bound promotion."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import shutil
import tempfile
from typing import Final

from ..audit.pipeline import audit_batch
from ..config import PipelineConfig
from ..db.pipeline import build_database
from ..errors import (
    InputFormatError,
    OutputConflictError,
    PipelineError,
    PromotionError,
)
from ..export.pipeline import export_database
from ..models import (
    ApprovalRecord,
    ArtifactRef,
    CandidateBuildRequest,
    CandidateRelease,
    DatabaseBuildRequest,
    ExportRequest,
    FormalRelease,
    ReleaseContract,
    VerificationCheck,
    VerificationReport,
)
from .hashing import sha256_file, write_manifest, write_sha256sums
from .packaging import write_deterministic_zip
from .transformers import transform_v117_release
from .verification import verify_release as _verify_release


V117_BASELINE_V116_ZIP_SHA256: Final[str] = (
    "5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae"
)


def _artifact(path: Path, kind: str) -> ArtifactRef:
    return ArtifactRef(
        path=path,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        kind=kind,
    )


def _direct_filename(value: str, field_name: str) -> str:
    if type(value) is not str or not value or Path(value).name != value:
        raise PipelineError(f"{field_name} must be a non-empty direct filename")
    return value


def _validate_contract_names(contract: ReleaseContract) -> None:
    names = (
        _direct_filename(contract.approval_filename, "approval_filename"),
        _direct_filename(contract.manifest_filename, "manifest_filename"),
        _direct_filename(contract.sha256sums_filename, "sha256sums_filename"),
        _direct_filename(contract.candidate_zip_filename, "candidate_zip_filename"),
        _direct_filename(contract.formal_zip_filename, "formal_zip_filename"),
    )
    if len(set(names)) != len(names):
        raise PipelineError("Release contract filenames must be unique")


def _database_filename(version: str) -> str:
    return f"Joy_M2_Complete_Question_DB_{version.replace('.', '_')}.sqlite3"


def _derived_artifacts(value) -> tuple[ArtifactRef, ...]:
    result = (
        value.csv,
        value.knowledge_markdown,
        value.import_report,
        value.project_state,
        value.audit_records,
        value.audit_report,
    )
    if value.taxonomy is not None:
        result += (value.taxonomy,)
    return result


def _manifest_payload(
    request: CandidateBuildRequest,
    audit_result,
    artifacts: tuple[ArtifactRef, ...],
) -> dict[str, object]:
    artifact_sha256 = {
        reference.path.name: reference.sha256 for reference in artifacts
    }
    profile = request.release_spec.release_version
    common: dict[str, object] = {
        "artifact_sha256": artifact_sha256,
        "release_status": "candidate",
        "release_version": profile,
        "schema_version": request.release_spec.schema_version,
    }
    evidence = audit_result.input_evidence
    if profile == "V1.17":
        common.update(
            {
                "approved_question_count": audit_result.report.candidate_count,
                "baseline_v116_sqlite_sha256": evidence.baseline_database.sha256,
                "baseline_v116_zip_sha256": V117_BASELINE_V116_ZIP_SHA256,
                "release_model": "transitional-dual-layer",
                "remaining_unmigrated_complete_questions": 452,
                "task4_candidate_sha256": evidence.candidate_json.sha256,
            }
        )
    elif profile == "V1.18":
        common.update(
            {
                "baseline_v117_sqlite_sha256": evidence.baseline_database.sha256,
                "complete_question_count": request.database_contract.expected_question_count,
                "legacy_compatibility_retained": True,
                "task6_imported_question_count": audit_result.report.candidate_count,
            }
        )
    else:
        raise PipelineError("Release candidate profile must be V1.17 or V1.18")
    if not all(field in common for field in request.release_contract.manifest_required_fields):
        raise PipelineError("candidate manifest cannot satisfy Release contract fields")
    return common


def _rebind(reference: ArtifactRef, old_root: Path, new_root: Path) -> ArtifactRef:
    relative = reference.path.relative_to(old_root)
    return ArtifactRef(
        path=new_root / relative,
        sha256=reference.sha256,
        size_bytes=reference.size_bytes,
        kind=reference.kind,
    )


def verify_release(
    release_dir: Path,
    contract: ReleaseContract,
) -> VerificationReport:
    """Independently verify one declared release directory."""

    return _verify_release(release_dir, contract)


def verify_candidate(candidate: CandidateRelease) -> VerificationReport:
    """Verify a candidate envelope and every file it binds without mutation."""

    if type(candidate) is not CandidateRelease:
        raise PipelineError("candidate must be a CandidateRelease")
    root = candidate.candidate_zip.path.parent
    checks: list[VerificationCheck] = []
    references = candidate.artifacts + (candidate.candidate_zip,)
    expected_paths: set[Path] = set()
    identities_valid = True
    same_root = True
    for reference in references:
        try:
            reference.path.relative_to(root)
        except ValueError:
            same_root = False
        expected_paths.add(reference.path)
        identities_valid = identities_valid and (
            reference.path.is_file()
            and reference.path.stat().st_size == reference.size_bytes
            and sha256_file(reference.path) == reference.sha256
        )
    actual_paths = {path for path in root.rglob("*") if path.is_file()}
    checks.extend(
        (
            VerificationCheck(
                "candidate_artifact_identity",
                same_root and identities_valid,
                "Candidate ArtifactRefs must bind files under one candidate root",
            ),
            VerificationCheck(
                "candidate_file_set",
                same_root and actual_paths == expected_paths,
                "candidate directory must contain exactly its declared artifacts",
            ),
        )
    )
    manifest = root / candidate.release_contract.manifest_filename
    checks.append(
        VerificationCheck(
            "candidate_manifest_binding",
            manifest.is_file()
            and candidate.candidate_manifest_sha256 == sha256_file(manifest),
            "CandidateRelease must bind the declared manifest",
        )
    )
    manifest_identity = False
    try:
        manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
        manifest_identity = (
            type(manifest_value) is dict
            and candidate.release_version == candidate.release_contract.profile
            and manifest_value.get("release_version") == candidate.release_version
            and manifest_value.get("release_status") == "candidate"
            and manifest_value.get("schema_version") == "complete-question-v1.0"
            and candidate.candidate_zip.path
            == root / candidate.release_contract.candidate_zip_filename
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise InputFormatError("release manifest is not valid UTF-8 JSON") from error
    except OSError:
        pass
    checks.append(
        VerificationCheck(
            "candidate_manifest_identity",
            manifest_identity,
            "Candidate version, contract, manifest identity, and ZIP name must agree",
        )
    )
    try:
        primitive = _verify_release(root, candidate.release_contract)
        checks.extend(primitive.checks)
    except PipelineError as error:
        checks.append(
            VerificationCheck(
                "candidate_release_structure",
                False,
                str(error),
            )
        )
    return VerificationReport(
        status="PASS" if all(check.passed for check in checks) else "FAIL",
        checks=tuple(checks),
    )


def build_candidate(request: CandidateBuildRequest) -> CandidateRelease:
    """Run Audit -> transform -> Database -> Export and atomically publish a candidate."""

    if type(request) is not CandidateBuildRequest:
        raise PipelineError("request must be a CandidateBuildRequest")
    _validate_contract_names(request.release_contract)
    if not request.run_id or Path(request.run_id).name != request.run_id:
        raise PipelineError("run_id must be a non-empty direct path component")
    target = request.config.require_staging_output(
        request.config.staging_root / request.run_id
    )
    if target.exists():
        raise OutputConflictError(f"candidate run already exists: {target}")
    request.config.staging_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{request.run_id}.", dir=request.config.staging_root)
    )
    try:
        audit_result = audit_batch(request.audit_request)
        if request.release_spec.release_version == "V1.17":
            record_batch = transform_v117_release(
                audit_result,
                request.v117_release_decision,
            )
        else:
            record_batch = audit_result.require_passed()
        database = build_database(
            DatabaseBuildRequest(
                batch=record_batch,
                baseline_database=request.audit_request.baseline_database,
                baseline_manifest=request.baseline_manifest,
                output_path=temporary / _database_filename(request.release_spec.release_version),
                release_spec=request.release_spec,
                contract=request.database_contract,
            )
        )
        exported = export_database(
            ExportRequest(
                database=database,
                audit_result=audit_result,
                record_batch=record_batch,
                output_dir=temporary,
                contract=request.export_contract,
            )
        )
        upstream = (database.database,) + _derived_artifacts(exported)
        if any(
            reference.kind not in request.release_contract.protected_artifact_kinds
            for reference in upstream
        ):
            raise PipelineError("Release contract does not protect every upstream artifact")
        manifest = write_manifest(
            temporary / request.release_contract.manifest_filename,
            _manifest_payload(request, audit_result, upstream),
        )
        protected = upstream + (manifest,)
        sums = write_sha256sums(
            temporary / request.release_contract.sha256sums_filename,
            protected,
        )
        candidate_zip = write_deterministic_zip(
            temporary / request.release_contract.candidate_zip_filename,
            temporary,
            protected + (sums,),
            request.release_contract.archive_root,
        )
        provisional = CandidateRelease(
            run_id=request.run_id,
            release_version=request.release_spec.release_version,
            release_contract=request.release_contract,
            candidate_manifest_sha256=manifest.sha256,
            verification_report=VerificationReport(status="PASS", checks=()),
            artifacts=protected + (sums,),
            candidate_zip=candidate_zip,
        )
        report = verify_candidate(provisional)
        if report.status != "PASS":
            raise PipelineError("candidate verification failed")
        if target.exists():
            raise OutputConflictError(f"candidate run already exists: {target}")
        temporary.replace(target)
        return CandidateRelease(
            run_id=request.run_id,
            release_version=request.release_spec.release_version,
            release_contract=request.release_contract,
            candidate_manifest_sha256=manifest.sha256,
            verification_report=report,
            artifacts=tuple(_rebind(ref, temporary, target) for ref in provisional.artifacts),
            candidate_zip=_rebind(candidate_zip, temporary, target),
        )
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def _approval_bytes(approval: ApprovalRecord) -> bytes:
    return (
        json.dumps(asdict(approval), ensure_ascii=False, sort_keys=True, indent=2)
        + "\n"
    ).encode("utf-8")


def _validate_approval(candidate: CandidateRelease, approval: ApprovalRecord) -> None:
    if type(approval) is not ApprovalRecord:
        raise PromotionError("approval must be an ApprovalRecord")
    try:
        approved_at = datetime.fromisoformat(approval.approved_at)
    except (TypeError, ValueError) as error:
        raise PromotionError("approval timestamp must be valid ISO-8601") from error
    if (
        approval.release_version != candidate.release_version
        or approval.candidate_manifest_sha256 != candidate.candidate_manifest_sha256
        or approval.approved_by != "Joy"
        or approved_at.utcoffset() is None
        or type(approval.scope) is not str
        or not approval.scope.strip()
    ):
        raise PromotionError("approval does not bind the candidate exactly")


def promote_candidate(
    candidate: CandidateRelease,
    approval: ApprovalRecord,
    config: PipelineConfig,
) -> FormalRelease:
    """Freshly verify and atomically promote an explicitly approved candidate."""

    if type(candidate) is not CandidateRelease or type(config) is not PipelineConfig:
        raise PromotionError("promotion requires CandidateRelease and PipelineConfig")
    if candidate.verification_report.status != "PASS":
        raise PromotionError("candidate stored verification did not pass")
    if verify_candidate(candidate).status != "PASS":
        raise PromotionError("candidate failed fresh verification")
    _validate_approval(candidate, approval)
    contract = candidate.release_contract
    _validate_contract_names(contract)
    try:
        target = config.new_formal_target(candidate.release_version)
    except PipelineError as error:
        raise PromotionError(str(error)) from error
    config.releases_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{candidate.release_version}.", dir=config.releases_root)
    )
    try:
        candidate_root = candidate.candidate_zip.path.parent
        payload_refs = tuple(
            reference
            for reference in candidate.artifacts
            if reference.kind not in {"manifest", "sha256sums", "zip"}
        )
        copied: list[ArtifactRef] = []
        for reference in payload_refs:
            relative = reference.path.relative_to(candidate_root)
            destination = temporary / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(reference.path, destination)
            copied.append(_artifact(destination, reference.kind))
        approval_path = temporary / contract.approval_filename
        approval_path.write_bytes(_approval_bytes(approval))
        approval_ref = _artifact(approval_path, "approval")

        candidate_manifest_path = candidate_root / contract.manifest_filename
        manifest_value = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
        manifest_value.update(
            {
                "approved_at": approval.approved_at,
                "approved_by": approval.approved_by,
                "approval_sha256": approval_ref.sha256,
                "candidate_manifest_sha256": candidate.candidate_manifest_sha256,
                "release_status": "formal",
            }
        )
        manifest_value["artifact_sha256"] = {
            reference.path.name: reference.sha256
            for reference in (*copied, approval_ref)
        }
        manifest_ref = write_manifest(
            temporary / contract.manifest_filename,
            manifest_value,
        )
        protected = tuple(copied) + (approval_ref, manifest_ref)
        sums_ref = write_sha256sums(
            temporary / contract.sha256sums_filename,
            protected,
        )
        zip_ref = write_deterministic_zip(
            temporary / contract.formal_zip_filename,
            temporary,
            protected + (sums_ref,),
            contract.archive_root,
        )
        report = verify_release(temporary, contract)
        if report.status != "PASS":
            raise PromotionError("formal release verification failed")
        if target.exists():
            raise PromotionError(f"formal release already exists: {target}")
        temporary.replace(target)
        rebound_manifest = _rebind(manifest_ref, temporary, target)
        final_hashes = tuple(
            _rebind(reference, temporary, target)
            for reference in protected + (sums_ref, zip_ref)
        )
        return FormalRelease(
            release_dir=target,
            manifest=rebound_manifest,
            verification_report=report,
            final_hashes=final_hashes,
        )
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
