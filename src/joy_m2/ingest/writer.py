"""Deterministic Task 9C V1.19 candidate writer."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import shutil
import sqlite3
import tempfile

from joy_m2.config import PipelineConfig
from joy_m2.errors import ImportApprovalError, InputFormatError, InputMissingError, OutputConflictError, PipelineError
from joy_m2.ingest.models import BatchImportManifest, ImportAdaptation, ImportCandidate, ImportFileEvidence, ImportIssue, ImportPreflightReport, ImportPreflightResult, as_plain_dict
from joy_m2.models import ArtifactRef

from .writer_models import ImportApproval, V119CandidateArtifacts, V119VerificationRequest, V119WriteRequest, V119WriterContract
from .writer_profiles import BASELINE_SHA256, BASELINE_SIZE_BYTES, FROZEN_SQLITE_HEADER_VERSION, TASK9_SCHEMA_SQL, atomic_rename_no_replace, canonical_json_bytes, canonical_json_file_bytes, relative_path, sha256_bytes, sha256_file
from .writer_verification import verify_v119_candidate


_CONTRACT = {
    "profile": "V1.19",
    "candidate_manifest_schema": "task9-v119-candidate-manifest-v1",
    "candidate_database_schema": "task9-v119-candidate-v1",
    "expected_user_version": 119,
    "database_filename": "Joy_M2_V1.19_candidate.sqlite3",
    "manifest_filename": "candidate_manifest.json",
    "sha256s_filename": "SHA256SUMS",
    "rollback_filename": "rollback.json",
    "image_root": "images/sha256",
    "required_baseline_tables": (
        "complete_question_corrections_v2", "complete_question_tags_v2",
        "complete_question_taxonomy_v2", "complete_questions_v2", "import_runs_v2",
        "question_topics", "questions", "release_metadata_v2", "sources", "topics",
    ),
    "required_candidate_tables": (
        "task9_import_batches_v1", "task9_import_candidates_v1",
        "task9_import_images_v1", "task9_import_taxonomy_v1",
    ),
    "required_candidate_views": ("task9_candidate_questions_v1",),
}


def _file_projection(evidence: ImportFileEvidence) -> dict[str, object]:
    return {"relative_path": evidence.relative_path, "sha256": evidence.sha256, "size_bytes": evidence.size_bytes, "kind": evidence.kind}


def _manifest_projection(manifest: BatchImportManifest) -> dict[str, object]:
    return {
        "schema_version": manifest.schema_version, "batch_id": manifest.batch_id,
        "project": manifest.project, "module": manifest.module, "chapter": manifest.chapter,
        "target_release_version": manifest.target_release_version,
        "candidate_records": [_file_projection(item) for item in manifest.candidate_records],
        "source_files": [_file_projection(item) for item in manifest.source_files],
        "answer_files": [_file_projection(item) for item in manifest.answer_files],
        "image_files": [_file_projection(item) for item in manifest.image_files],
        "teacher_notes_files": [_file_projection(item) for item in manifest.teacher_notes_files],
        "common_errors_files": [_file_projection(item) for item in manifest.common_errors_files],
        "language_policy": manifest.language_policy, "split_policy": manifest.split_policy,
        "difficulty_policy": manifest.difficulty_policy, "tag_policy": manifest.tag_policy,
        "answer_policy": manifest.answer_policy, "explanation_policy": manifest.explanation_policy,
    }


def _report_projection(report: ImportPreflightReport) -> dict[str, object]:
    result = {field.name: getattr(report, field.name) for field in fields(report) if field.name != "preflight_sha256"}
    result["adaptations"] = [as_plain_dict(item) for item in report.adaptations]
    return result


def _recomputed_digests(preflight: ImportPreflightResult) -> tuple[str, str]:
    manifest_sha256 = sha256_bytes(canonical_json_file_bytes(_manifest_projection(preflight.manifest)))
    groups = (
        preflight.manifest.candidate_records, preflight.manifest.source_files,
        preflight.manifest.answer_files, preflight.manifest.image_files,
        preflight.manifest.teacher_notes_files, preflight.manifest.common_errors_files,
    )
    file_evidence = tuple(sorted((item for group in groups for item in group), key=lambda item: item.relative_path))
    image_by_path = {item.relative_path: item for item in preflight.manifest.image_files}
    image_evidence = [
        {"proposed_question_id": candidate.proposed_question_id, "relative_path": path,
         "sha256": image_by_path[path].sha256, "size_bytes": image_by_path[path].size_bytes,
         "kind": image_by_path[path].kind, "role": role}
        for candidate in preflight.candidates
        for path, role in zip(candidate.image_paths, candidate.image_roles, strict=True)
    ]
    payload = {
        "schema": "task9-preflight-v1", "batch_id": preflight.manifest.batch_id,
        "target_release_version": preflight.manifest.target_release_version,
        "baseline": {"release_version": "V1.18", "schema_version": "complete-question-v1.0", "question_count": 497,
                     "sha256": preflight.baseline_database.sha256, "size_bytes": preflight.baseline_database.size_bytes,
                     "kind": preflight.baseline_database.kind},
        "manifest_policies": {name: getattr(preflight.manifest, name) for name in (
            "schema_version", "project", "module", "chapter", "language_policy", "split_policy",
            "difficulty_policy", "tag_policy", "answer_policy", "explanation_policy")},
        "candidate_record_order": [item.relative_path for item in preflight.manifest.candidate_records],
        "file_evidence": [as_plain_dict(item) for item in file_evidence],
        "candidates": [as_plain_dict(candidate) for candidate in preflight.candidates],
        "issues": [as_plain_dict(issue) for issue in preflight.issues],
        "duplicate_classifications": [
            {"candidate_id": candidate.proposed_question_id, "classification": "new_candidate", "reference_question_id": None, "evidence": None}
            for candidate in preflight.candidates
        ],
        "image_evidence": image_evidence,
        "report": _report_projection(preflight.report),
    }
    return manifest_sha256, sha256_bytes(canonical_json_file_bytes(payload))


def _reconstructs_exactly(value: object, expected_type: type) -> bool:
    if type(value) is not expected_type:
        return False
    try:
        reconstructed = expected_type(
            **{
                field.name: getattr(value, field.name)
                for field in fields(expected_type)
                if field.init
            }
        )
    except (
        AttributeError,
        OSError,
        PipelineError,
        RuntimeError,
        TypeError,
        ValueError,
    ):
        return False
    return reconstructed == value


def _nested_authority_valid(preflight: object, approval: object) -> bool:
    try:
        if not _reconstructs_exactly(approval, ImportApproval):
            return False
        if type(preflight) is not ImportPreflightResult:
            return False
        manifest = preflight.manifest
        report = preflight.report
        if not _reconstructs_exactly(manifest, BatchImportManifest):
            return False
        if not _reconstructs_exactly(preflight.baseline_database, ArtifactRef):
            return False
        if not isinstance(preflight.baseline_database.path, Path):
            return False
        if not _reconstructs_exactly(report, ImportPreflightReport):
            return False
        groups = (
            manifest.candidate_records,
            manifest.source_files,
            manifest.answer_files,
            manifest.image_files,
            manifest.teacher_notes_files,
            manifest.common_errors_files,
        )
        if any(
            not _reconstructs_exactly(item, ImportFileEvidence)
            for group in groups
            for item in group
        ):
            return False
        if any(
            not _reconstructs_exactly(item, ImportCandidate)
            for item in preflight.candidates
        ):
            return False
        if any(
            not _reconstructs_exactly(item, ImportIssue)
            for item in preflight.issues
        ):
            return False
        if any(
            not _reconstructs_exactly(item, ImportAdaptation)
            for item in report.adaptations
        ):
            return False
        return _reconstructs_exactly(preflight, ImportPreflightResult)
    except (AttributeError, PipelineError, RuntimeError, TypeError, ValueError):
        return False


def _validate_typed_authority(request: V119WriteRequest, config: PipelineConfig) -> None:
    if type(request) is not V119WriteRequest:
        raise PipelineError("request must be an exact V119WriteRequest")
    if type(config) is not PipelineConfig:
        raise PipelineError("config must be an exact PipelineConfig")
    if not _reconstructs_exactly(request, V119WriteRequest):
        raise PipelineError("request carrier is invalid")
    if not _reconstructs_exactly(config, PipelineConfig):
        raise PipelineError("config carrier is invalid")
    if not _reconstructs_exactly(request.contract, V119WriterContract):
        raise PipelineError("contract carrier is invalid")
    if type(request.contract) is not V119WriterContract or any(getattr(request.contract, name) != value for name, value in _CONTRACT.items()):
        raise PipelineError("contract does not match the exact V1.19 writer contract")
    preflight = request.preflight_result
    if not _nested_authority_valid(preflight, request.approval):
        raise ImportApprovalError("preflight authority carrier is invalid")
    report = preflight.report
    candidate_ids = tuple(item.proposed_question_id for item in preflight.candidates)
    evidence_groups = (
        preflight.manifest.candidate_records, preflight.manifest.source_files,
        preflight.manifest.answer_files, preflight.manifest.image_files,
        preflight.manifest.teacher_notes_files, preflight.manifest.common_errors_files,
    )
    for group in evidence_groups:
        for item in group:
            relative_path(item.relative_path)
    evidence_paths = tuple(sorted(
        item.relative_path for group in evidence_groups for item in group
    ))
    level_counts = tuple((level, sum(candidate.difficulty_level == level for candidate in preflight.candidates))
                         for level in range(1, 6) if any(candidate.difficulty_level == level for candidate in preflight.candidates))
    missing_answers = tuple(item.proposed_question_id for item in preflight.candidates if item.answer_status == "missing_from_source")
    missing_explanations = tuple(item.proposed_question_id for item in preflight.candidates if item.explanation_status == "missing")
    incomplete = tuple(item.proposed_question_id for item in preflight.candidates if item.enrichment_status == "incomplete")
    valid = (
        report.status == "READY FOR USER IMPORT APPROVAL" and report.batch_id == preflight.manifest.batch_id
        and report.baseline_version == "V1.18" and report.target_release_version == "V1.19" and report.before_count == 497
        and report.detected_count == len(preflight.candidates) and report.new_candidate_count == len(preflight.candidates)
        and report.duplicate_count == report.rejected_count == report.ambiguous_count == report.approved_count == 0
        and report.projected_after_count == 497 + len(preflight.candidates) and report.proposed_ids == candidate_ids
        and len(set(candidate_ids)) == len(candidate_ids) and report.readable_files == evidence_paths
        and report.unreadable_files == report.unsupported_files == report.missing_images == report.orphan_images == ()
        and report.teacher_notes_file_count == len(preflight.manifest.teacher_notes_files)
        and report.common_errors_file_count == len(preflight.manifest.common_errors_files)
        and report.level_counts == level_counts and report.missing_answers == missing_answers
        and report.missing_explanations == missing_explanations and report.incomplete_enrichments == incomplete
        and report.ambiguous_splits == ()
        and report.warnings == report.blocking_errors == () and preflight.issues == ()
        and request.approval.batch_id == preflight.manifest.batch_id
        and request.approval.preflight_sha256 == report.preflight_sha256
        and request.approval.target_release_version == "V1.19"
        and request.approval.statement == f"USER APPROVED IMPORT BATCH {preflight.manifest.batch_id} {report.preflight_sha256} V1.19"
    )
    if not valid:
        raise ImportApprovalError("preflight is not a closed READY approval authority")
    try:
        manifest_sha256, preflight_sha256 = _recomputed_digests(preflight)
    except (AttributeError, KeyError, PipelineError, TypeError, ValueError) as error:
        raise ImportApprovalError(
            "preflight digest authority cannot be reconstructed"
        ) from error
    if report.manifest_sha256 != manifest_sha256 or report.preflight_sha256 != preflight_sha256:
        raise ImportApprovalError("preflight digest authority cannot be reconstructed")


def _validate_paths(request: V119WriteRequest, config: PipelineConfig) -> tuple[Path, Path]:
    package_root = request.package_root.resolve(strict=False)
    if not package_root.exists():
        raise InputMissingError("package root does not exist")
    if not package_root.is_dir():
        raise InputFormatError("package root must be a directory")
    output = config.require_staging_output(request.output_dir)
    if output == config.staging_root:
        raise PipelineError("output must be a strict staging descendant")
    if output.exists():
        raise OutputConflictError("candidate output already exists")
    baseline = request.preflight_result.baseline_database.path.resolve(strict=False)
    for protected in (package_root, baseline):
        if output == protected or output.is_relative_to(protected) or protected.is_relative_to(output):
            raise PipelineError("writer paths must not overlap")
    return package_root, output


def _validate_baseline(reference: ArtifactRef) -> bytes:
    if type(reference) is not ArtifactRef or reference.kind != "sqlite" or reference.sha256 != BASELINE_SHA256 or reference.size_bytes != BASELINE_SIZE_BYTES:
        raise InputFormatError("frozen V1.18 ArtifactRef is invalid")
    path = reference.path
    if not path.is_file() or path.is_symlink():
        raise InputMissingError("frozen V1.18 database is missing")
    try:
        data = path.read_bytes()
    except OSError as error:
        raise InputFormatError("frozen V1.18 database is unreadable") from error
    if len(data) != reference.size_bytes or sha256_bytes(data) != reference.sha256:
        raise InputFormatError("frozen V1.18 database bytes do not match")
    database = None
    try:
        database = sqlite3.connect(":memory:")
        database.deserialize(data)
        metadata = dict(database.execute("SELECT key,value FROM release_metadata_v2"))
        valid = (database.execute("PRAGMA user_version").fetchone() == (118,)
                 and database.execute("PRAGMA integrity_check").fetchone() == ("ok",)
                 and database.execute("PRAGMA foreign_key_check").fetchall() == []
                 and database.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone() == (497,)
                 and metadata.get("release_version") == "V1.18"
                 and metadata.get("schema_version") == "complete-question-v1.0")
    except sqlite3.Error as error:
        raise InputFormatError("frozen V1.18 database cannot be inspected") from error
    finally:
        if database is not None:
            database.close()
    if not valid:
        raise InputFormatError("frozen V1.18 database identity is invalid")
    return data


def _image_plan(request: V119WriteRequest, package_root: Path):
    evidence = {item.relative_path: item for item in request.preflight_result.manifest.image_files}
    physical: dict[str, dict[str, object]] = {}
    bindings: list[dict[str, object]] = []
    digest_extensions: dict[str, str] = {}
    for candidate_order, candidate in enumerate(request.preflight_result.candidates):
        for image_order, (source_relative, expected_sha, role) in enumerate(zip(candidate.image_paths, candidate.image_sha256s, candidate.image_roles, strict=True)):
            source_relative = relative_path(source_relative)
            suffix = Path(source_relative).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png"}:
                raise InputFormatError("Task 9C image suffix is unsupported")
            extension = ".jpg" if suffix in {".jpg", ".jpeg"} else ".png"
            if digest_extensions.setdefault(expected_sha, extension) != extension:
                raise InputFormatError("one image digest has conflicting extensions")
            declared = evidence.get(source_relative)
            if declared is None or declared.kind != "image" or declared.sha256 != expected_sha:
                raise InputFormatError("image binding does not match manifest evidence")
            try:
                source = (package_root / source_relative).resolve(strict=True)
            except (OSError, RuntimeError) as error:
                raise InputMissingError("referenced image is missing") from error
            if not source.is_relative_to(package_root) or not source.is_file():
                raise InputFormatError("referenced image is not a contained regular file")
            try:
                data = source.read_bytes()
            except OSError as error:
                raise InputFormatError("referenced image is unreadable") from error
            digest = sha256_bytes(data)
            if len(data) != declared.size_bytes or digest != declared.sha256:
                raise InputFormatError("referenced image bytes do not match evidence")
            destination = f"{request.contract.image_root}/{digest[:2]}/{digest}{extension}"
            existing = physical.get(destination)
            if existing is not None and existing["bytes"] != data:
                raise InputFormatError("different image bytes claim one destination")
            physical.setdefault(destination, {"bytes": data, "sha256": digest, "size_bytes": len(data)})
            bindings.append({"batch_id": request.approval.batch_id, "proposed_question_id": candidate.proposed_question_id,
                             "candidate_order": candidate_order, "image_order": image_order,
                             "source_relative_path": source_relative, "candidate_relative_path": destination,
                             "sha256": digest, "size_bytes": len(data), "kind": "image", "role": role})
    return physical, tuple(bindings)


def _json_text(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _populate_database(path: Path, request: V119WriteRequest, bindings: tuple[dict[str, object], ...]) -> None:
    binding_paths: dict[str, list[str]] = {}
    for binding in bindings:
        binding_paths.setdefault(binding["proposed_question_id"], []).append(binding["candidate_relative_path"])
    with sqlite3.connect(path) as database:
        database.execute("PRAGMA foreign_keys=ON")
        database.execute("BEGIN IMMEDIATE")
        try:
            for statement in TASK9_SCHEMA_SQL:
                database.execute(statement)
            preflight = request.preflight_result
            report = preflight.report
            database.execute(
                "INSERT INTO task9_import_batches_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (request.approval.batch_id, "V1.19", request.contract.candidate_database_schema,
                 report.preflight_sha256, report.manifest_sha256, request.approval.statement,
                 "V1.18", preflight.baseline_database.sha256, 497, len(preflight.candidates),
                 report.projected_after_count, "candidate"),
            )
            for candidate_order, candidate in enumerate(preflight.candidates):
                values = [getattr(candidate, field.name) for field in fields(candidate)]
                for index in (16, 17, 18, 20):
                    values[index] = _json_text(values[index])
                row = (request.approval.batch_id, candidate_order, *values,
                       _json_text(binding_paths.get(candidate.proposed_question_id, [])), "candidate", 0)
                database.execute("INSERT INTO task9_import_candidates_v1 VALUES (" + ",".join("?" for _ in row) + ")", row)
            for binding in bindings:
                database.execute(
                    "INSERT INTO task9_import_images_v1 VALUES (?,?,?,?,?,?,?,?,?)",
                    (binding["batch_id"], binding["proposed_question_id"], binding["image_order"],
                     binding["source_relative_path"], binding["candidate_relative_path"], binding["sha256"],
                     binding["size_bytes"], "image", binding["role"]),
                )
            primary_types = tuple(sorted({item.primary_type for item in preflight.candidates}))
            tags = tuple(sorted({tag for item in preflight.candidates for tag in item.tags}))
            for kind, values in (("primary_type", primary_types), ("tag", tags)):
                for order, value in enumerate(values, start=1):
                    database.execute("INSERT INTO task9_import_taxonomy_v1 VALUES (?,?,?,?)",
                                     (request.approval.batch_id, kind, value, order))
            database.execute("PRAGMA user_version=119")
            database.commit()
        except Exception:
            database.rollback()
            raise
        if database.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise PipelineError("candidate SQLite integrity check failed")
        if database.execute("PRAGMA foreign_key_check").fetchall():
            raise PipelineError("candidate SQLite foreign key check failed")
        database.execute("VACUUM")
    with path.open("r+b") as handle:
        handle.seek(96)
        handle.write(FROZEN_SQLITE_HEADER_VERSION.to_bytes(4, "big"))


def _artifact(path: Path, kind: str) -> ArtifactRef:
    return ArtifactRef(path, sha256_file(path), path.stat().st_size, kind)


def _baseline_object(request: V119WriteRequest) -> dict[str, object]:
    reference = request.preflight_result.baseline_database
    return {"release_version": "V1.18", "question_count": 497, "schema_version": "complete-question-v1.0",
            "sqlite": {"sha256": reference.sha256, "size_bytes": reference.size_bytes, "kind": "sqlite"}}


def _build_manifest(request: V119WriteRequest, database: ArtifactRef, rollback: ArtifactRef,
                    images: tuple[ArtifactRef, ...], bindings: tuple[dict[str, object], ...], root: Path) -> dict[str, object]:
    preflight = request.preflight_result
    image_entries = []
    for image in images:
        relative = image.path.relative_to(root).as_posix()
        image_entries.append({
            "relative_path": relative, "sha256": image.sha256, "size_bytes": image.size_bytes, "kind": "image",
            "bindings": [
                {"proposed_question_id": binding["proposed_question_id"], "image_order": binding["image_order"],
                 "source_relative_path": binding["source_relative_path"], "role": binding["role"]}
                for binding in bindings if binding["candidate_relative_path"] == relative
            ],
        })
    report = preflight.report
    manifest = preflight.manifest
    return {
        "schema_version": request.contract.candidate_manifest_schema, "release_version": "V1.19",
        "release_status": "candidate", "release_model": "incremental-import-candidate",
        "batch": {"batch_id": manifest.batch_id, "preflight_sha256": report.preflight_sha256,
                  "manifest_sha256": report.manifest_sha256, "approval_statement": request.approval.statement,
                  "candidate_database_schema": request.contract.candidate_database_schema},
        "baseline": _baseline_object(request),
        "counts": {name: getattr(report, name) for name in (
            "before_count", "detected_count", "new_candidate_count", "duplicate_count", "rejected_count",
            "ambiguous_count", "approved_count", "projected_after_count")},
        "database": {"relative_path": database.path.relative_to(root).as_posix(), "sha256": database.sha256,
                     "size_bytes": database.size_bytes, "kind": "sqlite"},
        "images": image_entries,
        "candidate_record_evidence": [_file_projection(item) for item in manifest.candidate_records],
        "source_evidence": [_file_projection(item) for item in manifest.source_files],
        "answer_evidence": [_file_projection(item) for item in manifest.answer_files],
        "teacher_notes_evidence": [_file_projection(item) for item in manifest.teacher_notes_files],
        "common_errors_evidence": [_file_projection(item) for item in manifest.common_errors_files],
        "rollback": {"relative_path": rollback.path.relative_to(root).as_posix(), "sha256": rollback.sha256,
                     "size_bytes": rollback.size_bytes, "kind": "rollback"},
    }


def _final_artifact(reference: ArtifactRef, temporary: Path, output: Path) -> ArtifactRef:
    return ArtifactRef(output / reference.path.relative_to(temporary), reference.sha256, reference.size_bytes, reference.kind)


def build_v119_candidate(request: V119WriteRequest, config: PipelineConfig) -> V119CandidateArtifacts:
    """Build and independently verify one deterministic V1.19 candidate tree."""
    _validate_typed_authority(request, config)
    package_root, output = _validate_paths(request, config)
    baseline_bytes = _validate_baseline(request.preflight_result.baseline_database)
    physical_images, bindings = _image_plan(request, package_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        database_path = temporary / request.contract.database_filename
        database_path.write_bytes(baseline_bytes)
        _populate_database(database_path, request, bindings)
        database = _artifact(database_path, "sqlite")
        images_list = []
        for relative, identity in sorted(physical_images.items()):
            path = temporary / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(identity["bytes"])
            images_list.append(_artifact(path, "image"))
        images = tuple(images_list)
        artifact_paths = tuple(sorted((request.contract.database_filename, request.contract.manifest_filename,
                                       request.contract.sha256s_filename, request.contract.rollback_filename,
                                       *(item.path.relative_to(temporary).as_posix() for item in images))))
        rollback_path = temporary / request.contract.rollback_filename
        rollback_path.write_bytes(canonical_json_file_bytes({
            "schema_version": "task9-v119-rollback-v1", "action": "delete_unpromoted_candidate_tree",
            "batch_id": request.approval.batch_id, "preflight_sha256": request.approval.preflight_sha256,
            "baseline": _baseline_object(request), "candidate_artifacts": list(artifact_paths),
        }))
        rollback = _artifact(rollback_path, "rollback")
        manifest_path = temporary / request.contract.manifest_filename
        manifest_path.write_bytes(canonical_json_file_bytes(_build_manifest(request, database, rollback, images, bindings, temporary)))
        manifest = _artifact(manifest_path, "manifest")
        sums_path = temporary / request.contract.sha256s_filename
        sums_entries = tuple(sorted((database, manifest, rollback, *images), key=lambda item: item.path.relative_to(temporary).as_posix()))
        sums_path.write_text("".join(f"{item.sha256}  {item.path.relative_to(temporary).as_posix()}\n" for item in sums_entries),
                             encoding="utf-8", newline="")
        sha256sums = _artifact(sums_path, "sha256sums")
        verification = verify_v119_candidate(V119VerificationRequest(temporary, request.preflight_result, request.approval, request.contract), config)
        if verification.status != "PASS" or not all(check.passed for check in verification.checks):
            raise PipelineError("candidate verification did not pass")
        result = V119CandidateArtifacts(
            _final_artifact(database, temporary, output), _final_artifact(manifest, temporary, output),
            _final_artifact(sha256sums, temporary, output), _final_artifact(rollback, temporary, output),
            tuple(_final_artifact(item, temporary, output) for item in images), verification,
        )
        try:
            atomic_rename_no_replace(temporary, output)
        except FileExistsError as error:
            raise OutputConflictError("candidate output already exists") from error
        return result
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
