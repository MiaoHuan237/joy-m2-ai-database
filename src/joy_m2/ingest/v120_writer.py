"""Deterministic Task 10A V1.20 aggregate candidate writer."""

from dataclasses import fields
import errno
import json
from pathlib import Path
import shutil
import sqlite3
import stat
import tempfile
import unicodedata

from joy_m2.config import PipelineConfig
from joy_m2.errors import (
    ImportApprovalError,
    InputFormatError,
    InputMissingError,
    OutputConflictError,
    PipelineError,
)
from joy_m2.ingest.models import (
    ImportAdaptation,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
)
from joy_m2.models import ArtifactRef, VerificationReport

from .v120_models import (
    V120ApprovedBatch,
    V120BatchImportManifest,
    V120BatchLedgerEntry,
    V120CandidateArtifacts,
    V120CandidateBuildRequest,
    V120CandidateContract,
    V120CandidateVerificationRequest,
    V120EffectiveState,
    V120ImportApproval,
    V120ImportPreflightReport,
    V120ImportPreflightResult,
)
from .v120_verification import (
    _authority_expectations,
    _formal_baseline_valid,
    verify_v120_candidate,
)
from . import v120_verification as _independent_verification
from .v120_writer_profiles import (
    BASELINE_RELEASE_DIGEST,
    BASELINE_SHA256,
    BASELINE_SIZE_BYTES,
    CHECK_NAMES,
    TASK10_SCHEMA_SQL,
    canonical_json_bytes,
    canonical_json_file_bytes,
    image_destination,
    sha256_bytes,
    sha256_file,
)
from .writer_profiles import atomic_rename_no_replace


__all__ = ("build_v120_candidate",)


_BASELINE = {
    "release_version": "V1.19",
    "question_count": 502,
    "database_schema": "task9-v119-formal-v1",
    "sqlite": {
        "sha256": BASELINE_SHA256,
        "size_bytes": BASELINE_SIZE_BYTES,
        "kind": "sqlite",
    },
    "manifest": {
        "sha256": "cd048408df5e062592d5ed8553b3461860c876b0264660ab65c78c428584a510",
        "size_bytes": 3_242,
        "kind": "manifest",
    },
    "release_digest": BASELINE_RELEASE_DIGEST,
}


def _reconstructs_exactly(value: object, expected_type: type) -> bool:
    if type(value) is not expected_type:
        return False
    try:
        reconstructed = expected_type(**{
            field.name: getattr(value, field.name)
            for field in fields(expected_type)
            if field.init
        })
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


def _nested_authority_valid(batch: object) -> bool:
    try:
        if not _reconstructs_exactly(batch, V120ApprovedBatch):
            return False
        result = batch.preflight_result
        manifest = result.manifest
        state = result.effective_state
        report = result.report
        if not all((
            _reconstructs_exactly(batch.approval, V120ImportApproval),
            _reconstructs_exactly(result, V120ImportPreflightResult),
            _reconstructs_exactly(manifest, V120BatchImportManifest),
            _reconstructs_exactly(state, V120EffectiveState),
            _reconstructs_exactly(report, V120ImportPreflightReport),
            _reconstructs_exactly(state.baseline_database, ArtifactRef),
        )):
            return False
        groups = (
            manifest.candidate_records,
            manifest.source_files,
            manifest.answer_files,
            manifest.image_files,
            manifest.teacher_notes_files,
            manifest.common_errors_files,
        )
        return (
            all(
                _reconstructs_exactly(item, ImportFileEvidence)
                for group in groups
                for item in group
            )
            and all(
                _reconstructs_exactly(item, ImportCandidate)
                for item in result.candidates
            )
            and all(
                _reconstructs_exactly(item, ImportIssue)
                for item in result.issues
            )
            and all(
                _reconstructs_exactly(item, ImportAdaptation)
                for item in report.adaptations
            )
            and all(
                _reconstructs_exactly(item, V120BatchLedgerEntry)
                and _reconstructs_exactly(item.approval, V120ImportApproval)
                for item in state.batch_ledger
            )
        )
    except (AttributeError, PipelineError, RuntimeError, TypeError, ValueError):
        return False


def _preflight_authority_closed(approved: V120ApprovedBatch) -> bool:
    result = approved.preflight_result
    report = result.report
    manifest = result.manifest
    candidates = result.candidates
    candidate_ids = tuple(item.proposed_question_id for item in candidates)
    groups = (
        manifest.candidate_records,
        manifest.source_files,
        manifest.answer_files,
        manifest.image_files,
        manifest.teacher_notes_files,
        manifest.common_errors_files,
    )
    evidence_paths = tuple(sorted(
        item.relative_path for group in groups for item in group
    ))
    level_counts = tuple(
        (level, sum(item.difficulty_level == level for item in candidates))
        for level in range(1, 6)
        if any(item.difficulty_level == level for item in candidates)
    )
    missing_answers = tuple(
        item.proposed_question_id
        for item in candidates
        if item.answer_status == "missing_from_source"
    )
    missing_explanations = tuple(
        item.proposed_question_id
        for item in candidates
        if item.explanation_status == "missing"
    )
    incomplete_enrichments = tuple(
        item.proposed_question_id
        for item in candidates
        if item.enrichment_status == "incomplete"
    )
    return (
        report.status == "READY FOR USER IMPORT APPROVAL"
        and report.batch_id == manifest.batch_id
        and report.baseline_version == "V1.19"
        and report.baseline_release_digest == BASELINE_RELEASE_DIGEST
        and report.baseline_question_count == 502
        and report.target_release_version == "V1.20"
        and report.before_count == result.effective_state.projected_question_count
        and report.detected_count == len(candidates)
        and report.new_candidate_count == len(candidates)
        and report.duplicate_count == 0
        and report.rejected_count == 0
        and report.ambiguous_count == 0
        and report.approved_count == 0
        and report.projected_after_count == report.before_count + len(candidates)
        and report.proposed_ids == candidate_ids
        and len(set(candidate_ids)) == len(candidate_ids)
        and report.readable_files == evidence_paths
        and report.unreadable_files == ()
        and report.unsupported_files == ()
        and report.teacher_notes_file_count == len(manifest.teacher_notes_files)
        and report.common_errors_file_count == len(manifest.common_errors_files)
        and report.ambiguous_splits == ()
        and report.missing_answers == missing_answers
        and report.missing_explanations == missing_explanations
        and report.incomplete_enrichments == incomplete_enrichments
        and report.missing_images == ()
        and report.orphan_images == ()
        and report.level_counts == level_counts
        and report.warnings == ()
        and report.blocking_errors == ()
        and result.issues == ()
    )


def _normalized_text_sha256(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for line in normalized.split("\n"):
        stripped = line.strip(" \t\v\f")
        parts: list[str] = []
        start = 0
        for index, character in enumerate(stripped):
            if character in " \t\v\f":
                if start != index:
                    parts.append(stripped[start:index])
                start = index + 1
        if start != len(stripped):
            parts.append(stripped[start:])
        lines.append(" ".join(parts))
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return sha256_bytes("\n".join(lines).encode("utf-8"))


def _collision_authority_valid(
    batches: tuple[V120ApprovedBatch, ...],
    baseline_path: Path,
) -> bool:
    try:
        with sqlite3.connect(baseline_path) as database:
            rows = tuple(database.execute(
                "SELECT question_id,source_id,source_question_number,source_section,"
                "source_fragment_hash,normalized_text_sha256,question_text_original,"
                "source_image_paths_json,source_image_sha256s_json,source_image_roles_json "
                "FROM formal_complete_questions_v119 ORDER BY formal_order"
            ))
        ids: set[str] = set()
        locators: dict[tuple[str, str, str], tuple[str, bool]] = {}
        fragments: dict[str, tuple[str, bool]] = {}
        normalized: set[str] = set()
        image_claims: dict[tuple[str, str], str] = {}
        for row in rows:
            reference_id = row[0]
            ids.add(reference_id)
            locators[(row[1], row[2], row[3])] = (reference_id, True)
            if row[4]:
                fragments[row[4]] = (reference_id, True)
            normalized.add(row[5] or _normalized_text_sha256(row[6]))
            paths = () if row[7] is None else json.loads(row[7])
            digests = () if row[8] is None else json.loads(row[8])
            roles = () if row[9] is None else json.loads(row[9])
            if all(type(item) is dict for item in paths):
                image_values = tuple(
                    (item["path"], item["sha256"], item["role"])
                    for item in paths
                    if set(item) == {"path", "role", "sha256"}
                )
                if len(image_values) != len(paths):
                    return False
            elif all(type(item) is str for item in paths):
                image_values = (
                    tuple(zip(paths, digests, roles, strict=True))
                    if digests or roles
                    else ()
                )
            else:
                return False
            for path, digest, role in image_values:
                image_claims[(path, role)] = digest

        for approved in batches:
            expected_adaptations: list[ImportAdaptation] = []
            for candidate in approved.preflight_result.candidates:
                locator = (
                    candidate.source_id,
                    candidate.source_question_number,
                    candidate.source_section,
                )
                locator_reference = locators.get(locator)
                fragment_reference = fragments.get(candidate.source_fragment_hash)
                allowed_adaptation = (
                    locator_reference is not None
                    and locator_reference == fragment_reference
                    and locator_reference[1]
                    and candidate.normalized_text_sha256 not in normalized
                )
                if allowed_adaptation:
                    reference_id = locator_reference[0]
                    expected_adaptations.append(ImportAdaptation(
                        candidate.proposed_question_id,
                        reference_id,
                        "adapted",
                        "matched=source_locator+source_fragment_hash;"
                        f"candidate_normalized_text_sha256={candidate.normalized_text_sha256};"
                        f"reference_normalized_text_sha256="
                        f"{next((row[5] or _normalized_text_sha256(row[6]) for row in rows if row[0] == reference_id), '')}",
                        "stable_source_identity_matches_with_transformed_text",
                    ))
                if (
                    candidate.proposed_question_id in ids
                    or candidate.normalized_text_sha256 in normalized
                    or ((locator_reference is not None or fragment_reference is not None) and not allowed_adaptation)
                ):
                    return False
                for path, digest, role in zip(
                    candidate.image_paths,
                    candidate.image_sha256s,
                    candidate.image_roles,
                    strict=True,
                ):
                    prior = image_claims.get((path, role))
                    if prior is not None and prior != digest:
                        return False
                    image_claims[(path, role)] = digest
                ids.add(candidate.proposed_question_id)
                locators[locator] = (candidate.proposed_question_id, False)
                fragments[candidate.source_fragment_hash] = (
                    candidate.proposed_question_id,
                    False,
                )
                normalized.add(candidate.normalized_text_sha256)
            if tuple(sorted(expected_adaptations, key=lambda item: (
                item.candidate_id,
                item.reference_question_id,
                item.adaptation_kind,
                item.evidence,
                item.reason,
            ))) != approved.preflight_result.report.adaptations:
                return False
        return True
    except (json.JSONDecodeError, OSError, PipelineError, sqlite3.Error, TypeError, ValueError):
        return False


def _has_symlink_component(path: Path, base: Path) -> bool:
    del base
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _cleanup_owned_private_tree(
    expected_path: Path,
    parent: Path,
    identity: tuple[int, int],
) -> None:
    """Remove only the private directory inode created by this writer call."""
    try:
        candidates = tuple(parent.iterdir())
    except OSError:
        return
    for candidate in candidates:
        try:
            metadata = candidate.lstat()
            if (
                (metadata.st_dev, metadata.st_ino) != identity
                or not stat.S_ISDIR(metadata.st_mode)
                or stat.S_ISLNK(metadata.st_mode)
            ):
                continue
            shutil.rmtree(candidate)
            return
        except OSError:
            continue


def _has_candidate_ancestor(
    path: Path,
    staging_root: Path,
    contract: V120CandidateContract,
) -> bool:
    current = path.parent
    while current != staging_root and current.is_relative_to(staging_root):
        manifest = current / contract.manifest_filename
        database = current / contract.database_filename
        if manifest.is_file() and database.is_file():
            try:
                payload = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                return True
            if (
                type(payload) is dict
                and payload.get("schema_version") == contract.candidate_manifest_schema
                and payload.get("release_version") == "V1.20"
                and payload.get("release_status") == "candidate"
            ):
                return True
        current = current.parent
    return False


def _validate_request(
    request: V120CandidateBuildRequest,
    config: PipelineConfig,
) -> tuple[Path, tuple[V120ApprovedBatch, ...], dict[str, bytes], dict[str, object]]:
    if type(request) is not V120CandidateBuildRequest:
        raise PipelineError("request must be an exact V120CandidateBuildRequest")
    if type(config) is not PipelineConfig or not _reconstructs_exactly(config, PipelineConfig):
        raise PipelineError("config must be an exact PipelineConfig")
    if not _reconstructs_exactly(request.contract, V120CandidateContract):
        raise PipelineError("contract carrier does not match the fixed V1.20 authority")
    if not _reconstructs_exactly(request, V120CandidateBuildRequest):
        raise PipelineError("build request carrier is invalid")
    batches = request.approved_batches
    if not batches or any(
        not _nested_authority_valid(batch)
        or not _preflight_authority_closed(batch)
        for batch in batches
    ):
        raise ImportApprovalError("approved batch authority carrier is invalid")

    validity, authority, identity = _authority_expectations(batches)
    if identity is None or not all(validity.values()):
        raise ImportApprovalError("approved batch prefix does not reconstruct exactly")

    output = request.output_dir
    configured_staging = config.repo_root / "data" / "staging"
    if (
        not isinstance(output, Path)
        or _has_symlink_component(configured_staging, config.repo_root)
        or _has_symlink_component(output, config.repo_root)
    ):
        raise PipelineError("candidate output must use a symlink-free path")
    try:
        resolved = output.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise PipelineError("candidate output cannot be resolved safely") from error
    if output.exists() or output.is_symlink():
        raise OutputConflictError("candidate output already exists")
    if (
        resolved == config.staging_root
        or not resolved.is_relative_to(config.staging_root)
        or resolved.is_relative_to(config.releases_root / "V1.20")
        or _has_candidate_ancestor(resolved, config.staging_root, request.contract)
    ):
        raise PipelineError("candidate output must be a strict staging descendant")
    protected = (
        batches[0].preflight_result.effective_state.baseline_database.path,
        *(batch.package_root for batch in batches),
    )
    for path in protected:
        try:
            target = path.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise InputMissingError("a protected writer input is missing") from error
        if resolved == target or resolved.is_relative_to(target) or target.is_relative_to(resolved):
            raise PipelineError("candidate output overlaps a protected writer input")
    if not output.parent.is_dir() or _has_symlink_component(output.parent, config.repo_root):
        raise PipelineError("candidate output parent must be an existing symlink-free directory")

    verification_request = V120CandidateVerificationRequest(output, batches, request.contract)
    if not _formal_baseline_valid(verification_request, output, config):
        raise InputFormatError("formal V1.19 baseline authority is invalid")
    baseline_path = batches[0].preflight_result.effective_state.baseline_database.path
    if not _collision_authority_valid(batches, baseline_path):
        raise ImportApprovalError("approved batch collision authority is invalid")
    return resolved, batches, authority, identity


def _image_plan(
    batches: tuple[V120ApprovedBatch, ...],
    image_root: str,
) -> dict[str, bytes]:
    physical: dict[str, bytes] = {}
    for batch in batches:
        manifest = batch.preflight_result.manifest
        evidence = {item.relative_path: item for item in manifest.image_files}
        package_root = batch.package_root.resolve(strict=True)
        for candidate in batch.preflight_result.candidates:
            for source, expected_digest in zip(
                candidate.image_paths,
                candidate.image_sha256s,
                strict=True,
            ):
                declared = evidence.get(source)
                path = batch.package_root / source
                try:
                    resolved = path.resolve(strict=True)
                    if (
                        declared is None
                        or declared.kind != "image"
                        or path.is_symlink()
                        or _has_symlink_component(path, batch.package_root)
                        or not resolved.is_relative_to(package_root)
                        or not resolved.is_file()
                    ):
                        raise InputFormatError("image source does not bind package evidence")
                    data = resolved.read_bytes()
                except InputFormatError:
                    raise
                except (OSError, RuntimeError) as error:
                    raise InputMissingError("image source cannot be read") from error
                digest = sha256_bytes(data)
                if (
                    declared.sha256 != expected_digest
                    or declared.sha256 != digest
                    or declared.size_bytes != len(data)
                ):
                    raise InputFormatError("image source bytes do not bind package evidence")
                destination = image_destination(image_root, source, digest)
                if destination in physical and physical[destination] != data:
                    raise InputFormatError("different image bytes claim one destination")
                physical[destination] = data
    return physical


def _json_text(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _populate_database(
    path: Path,
    batches: tuple[V120ApprovedBatch, ...],
    identity: dict[str, object],
) -> None:
    candidate_projection = {
        (item["batch_ordinal"], item["batch_id"], item["batch_candidate_order"]): item
        for item in identity["candidate_projection"]
    }
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        for statement in TASK10_SCHEMA_SQL[:-1]:
            connection.execute(statement)
        cumulative = 0
        for ordinal, batch in enumerate(batches, start=1):
            result = batch.preflight_result
            approval = batch.approval
            cumulative += len(result.candidates)
            connection.execute(
                "INSERT INTO task10_v120_batch_ledger_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    ordinal,
                    approval.batch_id,
                    "V1.20",
                    "task10-v120-candidate-v1",
                    approval.parent_candidate_digest,
                    approval.preflight_sha256,
                    result.report.manifest_sha256,
                    approval.statement,
                    "V1.19",
                    BASELINE_SHA256,
                    BASELINE_RELEASE_DIGEST,
                    502,
                    len(result.candidates),
                    cumulative,
                    502 + cumulative,
                    "candidate",
                ),
            )
            for order, candidate in enumerate(result.candidates):
                projection = candidate_projection[(ordinal, approval.batch_id, order)]
                values = [getattr(candidate, field.name) for field in fields(ImportCandidate)]
                for index in (16, 17, 18, 20):
                    values[index] = _json_text(values[index])
                row = (
                    ordinal,
                    approval.batch_id,
                    order,
                    projection["aggregate_order"],
                    *values,
                    _json_text(projection["candidate_image_paths"]),
                    "candidate",
                    0,
                )
                connection.execute(
                    "INSERT INTO task10_v120_candidates_v1 VALUES ("
                    + ",".join("?" for _ in row)
                    + ")",
                    row,
                )
                image_evidence = {
                    item.relative_path: item for item in result.manifest.image_files
                }
                for image_order, (source, digest, role, destination) in enumerate(zip(
                    candidate.image_paths,
                    candidate.image_sha256s,
                    candidate.image_roles,
                    projection["candidate_image_paths"],
                    strict=True,
                )):
                    evidence = image_evidence[source]
                    connection.execute(
                        "INSERT INTO task10_v120_images_v1 VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            ordinal,
                            approval.batch_id,
                            candidate.proposed_question_id,
                            image_order,
                            source,
                            destination,
                            digest,
                            evidence.size_bytes,
                            "image",
                            role,
                        ),
                    )
            primary_types = tuple(sorted({
                candidate.primary_type for candidate in result.candidates
            }))
            tags = tuple(sorted({
                tag for candidate in result.candidates for tag in candidate.tags
            }))
            for kind, values in (("primary_type", primary_types), ("tag", tags)):
                for sort_order, value in enumerate(values, start=1):
                    connection.execute(
                        "INSERT INTO task10_v120_taxonomy_v1 VALUES (?,?,?,?,?,?)",
                        (
                            ordinal,
                            approval.batch_id,
                            kind,
                            value,
                            sort_order,
                            "candidate",
                        ),
                    )
        connection.execute(TASK10_SCHEMA_SQL[-1])
        connection.execute("PRAGMA user_version=120")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _artifact(path: Path, kind: str) -> ArtifactRef:
    return ArtifactRef(path, sha256_file(path), path.stat().st_size, kind)


def _artifact_projection(reference: ArtifactRef, root: Path) -> dict[str, object]:
    return {
        "relative_path": reference.path.relative_to(root).as_posix(),
        "sha256": reference.sha256,
        "size_bytes": reference.size_bytes,
        "kind": reference.kind,
    }


def _ledger_entries(
    batches: tuple[V120ApprovedBatch, ...],
) -> tuple[V120BatchLedgerEntry, ...]:
    cumulative = 0
    result = []
    for ordinal, batch in enumerate(batches, start=1):
        cumulative += len(batch.preflight_result.candidates)
        result.append(V120BatchLedgerEntry(
            ordinal,
            batch.approval.batch_id,
            batch.approval.parent_candidate_digest,
            batch.approval.preflight_sha256,
            batch.preflight_result.report.manifest_sha256,
            batch.approval,
            len(batch.preflight_result.candidates),
            cumulative,
            502 + cumulative,
        ))
    return tuple(result)


def _final(reference: ArtifactRef, temporary: Path, output: Path) -> ArtifactRef:
    return ArtifactRef(
        output / reference.path.relative_to(temporary),
        reference.sha256,
        reference.size_bytes,
        reference.kind,
    )


def build_v120_candidate(
    request: V120CandidateBuildRequest,
    config: PipelineConfig,
) -> V120CandidateArtifacts:
    """Build, independently verify, and atomically publish the first V1.20 prefix."""
    output, batches, authority_bytes, identity = _validate_request(request, config)
    physical_images = _image_plan(batches, request.contract.image_root)
    baseline = batches[0].preflight_result.effective_state.baseline_database
    try:
        baseline_bytes = baseline.path.read_bytes()
    except OSError as error:
        raise InputMissingError("formal V1.19 database cannot be read") from error
    if len(baseline_bytes) != BASELINE_SIZE_BYTES or sha256_bytes(baseline_bytes) != BASELINE_SHA256:
        raise InputFormatError("formal V1.19 database bytes changed during validation")

    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    temporary_stat = temporary.lstat()
    temporary_identity = (temporary_stat.st_dev, temporary_stat.st_ino)
    try:
        if _has_symlink_component(temporary, config.repo_root):
            raise PipelineError("private candidate root is not symlink-free")
        database_path = temporary / request.contract.database_filename
        database_path.write_bytes(baseline_bytes)
        _populate_database(database_path, batches, identity)
        database = _artifact(database_path, "sqlite")

        authority_refs = []
        for relative, content in sorted(authority_bytes.items()):
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            authority_refs.append(_artifact(
                target,
                "approval" if target.name == "approval.json" else "preflight",
            ))

        image_refs = []
        for relative, content in sorted(physical_images.items()):
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            image_refs.append(_artifact(target, "image"))

        digest = sha256_bytes(canonical_json_file_bytes(identity))
        ledger = _ledger_entries(batches)
        state = V120EffectiveState(
            baseline,
            digest,
            ledger,
            identity["counts"]["new_candidate_count"],
            identity["counts"]["projected_question_count"],
        )
        fixed_paths = [
            database.path.relative_to(temporary).as_posix(),
            *(item.path.relative_to(temporary).as_posix() for item in authority_refs),
            *(item.path.relative_to(temporary).as_posix() for item in image_refs),
            request.contract.manifest_filename,
            request.contract.sha256s_filename,
            request.contract.rollback_filename,
        ]
        rollback_path = temporary / request.contract.rollback_filename
        rollback_path.write_bytes(canonical_json_file_bytes({
            "schema_version": request.contract.rollback_schema,
            "action": "delete_unpromoted_v120_candidate_tree_if_digest_matches",
            "candidate_digest": digest,
            "protected_baseline": _BASELINE,
            "candidate_artifacts": sorted(fixed_paths),
        }))
        rollback = _artifact(rollback_path, "rollback")

        manifest_path = temporary / request.contract.manifest_filename
        manifest_path.write_bytes(canonical_json_file_bytes({
            "schema_version": request.contract.candidate_manifest_schema,
            "release_version": "V1.20",
            "release_status": "candidate",
            "release_model": "append-only-multi-batch-candidate",
            "baseline": _BASELINE,
            "candidate_digest": digest,
            "counts": identity["counts"],
            "batch_ledger": identity["batch_ledger"],
            "database": _artifact_projection(database, temporary),
            "images": [
                _artifact_projection(item, temporary) for item in image_refs
            ],
            "batch_authority_artifacts": [
                _artifact_projection(item, temporary) for item in authority_refs
            ],
            "rollback": _artifact_projection(rollback, temporary),
            "verification": {
                "authority": "verify_v120_candidate",
                "check_names": list(CHECK_NAMES),
                "required_status": "PASS",
            },
        }))
        manifest = _artifact(manifest_path, "manifest")

        covered = sorted(
            path for path in temporary.rglob("*")
            if path.is_file() and path.name != request.contract.sha256s_filename
        )
        sums_path = temporary / request.contract.sha256s_filename
        sums_path.write_text(
            "".join(
                f"{sha256_file(path)}  {path.relative_to(temporary).as_posix()}\n"
                for path in covered
            ),
            encoding="utf-8",
            newline="\n",
        )
        sha256sums = _artifact(sums_path, "sha256sums")

        verification_request = V120CandidateVerificationRequest(
            temporary, batches, request.contract,
        )
        verification = verify_v120_candidate(verification_request, config)
        if (
            type(verification) is not VerificationReport
            or verification.status != "PASS"
            or tuple(check.name for check in verification.checks) != CHECK_NAMES
            or not all(check.passed for check in verification.checks)
        ):
            raise PipelineError("private candidate verification did not pass")
        final_validity, final_authority, final_identity = _authority_expectations(
            batches
        )
        if (
            final_identity is None
            or not all(final_validity.values())
            or final_authority != authority_bytes
            or final_identity != identity
        ):
            raise InputFormatError(
                "approved canonical package changed before publication"
            )
        final_verification = _independent_verification.verify_v120_candidate(
            verification_request, config,
        )
        if (
            type(final_verification) is not VerificationReport
            or final_verification.status != "PASS"
            or tuple(check.name for check in final_verification.checks) != CHECK_NAMES
            or not all(check.passed for check in final_verification.checks)
        ):
            raise PipelineError(
                "private candidate changed after its first verification"
            )

        result = V120CandidateArtifacts(
            _final(database, temporary, output),
            _final(manifest, temporary, output),
            _final(sha256sums, temporary, output),
            _final(rollback, temporary, output),
            tuple(_final(item, temporary, output) for item in authority_refs),
            tuple(_final(item, temporary, output) for item in image_refs),
            state,
            final_verification,
        )
        try:
            atomic_rename_no_replace(temporary, output)
        except OSError as error:
            if error.errno in {errno.EEXIST, errno.ENOTEMPTY}:
                raise OutputConflictError("candidate output already exists") from error
            raise PipelineError("candidate output could not be published atomically") from error
        return result
    except Exception:
        _cleanup_owned_private_tree(
            temporary, output.parent, temporary_identity,
        )
        raise
