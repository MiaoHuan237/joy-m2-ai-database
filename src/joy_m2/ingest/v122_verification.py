"""Independent read-only V1.22 candidate verification boundary."""

from dataclasses import fields
import json
from pathlib import Path
import sqlite3
import unicodedata

from joy_m2.config import PipelineConfig
from joy_m2.errors import InputFormatError, InputMissingError, PipelineError
from joy_m2.ingest.models import (
    ImportAdaptation,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
    as_plain_dict,
)
from joy_m2.models import ArtifactRef, VerificationCheck, VerificationReport

from .v122_models import (
    V122ApprovedBatch,
    V122BatchImportManifest,
    V122BatchLedgerEntry,
    V122CandidateContract,
    V122CandidateVerificationRequest,
    V122EffectiveState,
    V122ImportApproval,
    V122ImportPreflightReport,
    V122ImportPreflightResult,
)
from .v122_writer_profiles import (
    _genesis_digest,
    BASELINE_MANIFEST_SHA256,
    BASELINE_MANIFEST_SIZE_BYTES,
    BASELINE_RELEASE_DIGEST,
    BASELINE_SHA256,
    BASELINE_SIZE_BYTES,
    CHECK_NAMES,
    GENESIS_DIGEST,
    TASK12_SCHEMA_SQL,
    canonical_json_bytes,
    canonical_json_file_bytes,
    image_destination,
    is_sha256,
    normalized_sql,
    relative_path,
    sha256_bytes,
    sha256_file,
)


__all__ = ("verify_v122_candidate",)

_BASELINE = {
    "release_version": "V1.21",
    "question_count": 591,
    "database_schema": "task11-v121-formal-v1",
    "sqlite": {
        "sha256": BASELINE_SHA256,
        "size_bytes": BASELINE_SIZE_BYTES,
        "kind": "sqlite",
    },
    "manifest": {
        "sha256": BASELINE_MANIFEST_SHA256,
        "size_bytes": BASELINE_MANIFEST_SIZE_BYTES,
        "kind": "manifest",
    },
    "release_digest": BASELINE_RELEASE_DIGEST,
}
_CONTRACT = {
    "profile": "V1.22",
    "baseline_release_version": "V1.21",
    "baseline_question_count": 591,
    "baseline_database_sha256": BASELINE_SHA256,
    "baseline_database_size_bytes": BASELINE_SIZE_BYTES,
    "baseline_manifest_sha256": BASELINE_MANIFEST_SHA256,
    "baseline_manifest_size_bytes": BASELINE_MANIFEST_SIZE_BYTES,
    "baseline_release_digest": BASELINE_RELEASE_DIGEST,
    "canonical_manifest_schema": "task12-v122-import-manifest-v1",
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
    "required_candidate_tables": (
        "task12_v122_batch_ledger_v1",
        "task12_v122_candidates_v1",
        "task12_v122_images_v1",
        "task12_v122_taxonomy_v1",
    ),
    "required_candidate_views": ("task12_candidate_questions_v122",),
}


def _plain(value: object) -> object:
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    return value


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
        if not _reconstructs_exactly(batch, V122ApprovedBatch):
            return False
        result = batch.preflight_result
        manifest = result.manifest
        state = result.effective_state
        report = result.report
        groups = (
            manifest.candidate_records,
            manifest.source_files,
            manifest.answer_files,
            manifest.image_files,
            manifest.teacher_notes_files,
            manifest.common_errors_files,
        )
        return (
            _reconstructs_exactly(batch.approval, V122ImportApproval)
            and _reconstructs_exactly(result, V122ImportPreflightResult)
            and _reconstructs_exactly(manifest, V122BatchImportManifest)
            and _reconstructs_exactly(state, V122EffectiveState)
            and _reconstructs_exactly(report, V122ImportPreflightReport)
            and _reconstructs_exactly(state.baseline_database, ArtifactRef)
            and all(
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
                _reconstructs_exactly(item, V122BatchLedgerEntry)
                and _reconstructs_exactly(item.approval, V122ImportApproval)
                for item in state.batch_ledger
            )
        )
    except (AttributeError, PipelineError, RuntimeError, TypeError, ValueError):
        return False


def _preflight_authority_closed(approved: V122ApprovedBatch) -> bool:
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
        and report.baseline_version == "V1.21"
        and report.baseline_release_digest == BASELINE_RELEASE_DIGEST
        and report.baseline_question_count == 591
        and report.target_release_version == "V1.22"
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


def _exact_json(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return set(actual) == set(expected) and all(
            _exact_json(actual[key], value) for key, value in expected.items()
        )
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            _exact_json(left, right)
            for left, right in zip(actual, expected, strict=True)
        )
    return actual == expected


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


def _file_projection(value: ImportFileEvidence) -> dict[str, object]:
    return {
        "relative_path": value.relative_path,
        "sha256": value.sha256,
        "size_bytes": value.size_bytes,
        "kind": value.kind,
    }


def _manifest_projection(manifest: object) -> dict[str, object]:
    groups = {
        name: [_file_projection(item) for item in getattr(manifest, name)]
        for name in (
            "candidate_records", "source_files", "answer_files", "image_files",
            "teacher_notes_files", "common_errors_files",
        )
    }
    return {
        "schema_version": manifest.schema_version,
        "batch_id": manifest.batch_id,
        "project": manifest.project,
        "module": manifest.module,
        "chapter": manifest.chapter,
        "target_release_version": manifest.target_release_version,
        **groups,
        "language_policy": manifest.language_policy,
        "split_policy": manifest.split_policy,
        "difficulty_policy": manifest.difficulty_policy,
        "tag_policy": manifest.tag_policy,
        "answer_policy": manifest.answer_policy,
        "explanation_policy": manifest.explanation_policy,
    }


def _report_projection(report: object) -> dict[str, object]:
    return {
        field.name: _plain(getattr(report, field.name))
        for field in fields(report)
        if field.name != "preflight_sha256"
    }


def _preflight_payload(approved: V122ApprovedBatch) -> dict[str, object]:
    result = approved.preflight_result
    manifest = result.manifest
    groups = (
        manifest.candidate_records, manifest.source_files, manifest.answer_files,
        manifest.image_files, manifest.teacher_notes_files, manifest.common_errors_files,
    )
    evidence = sorted(
        (_file_projection(item) for group in groups for item in group),
        key=lambda item: item["relative_path"],
    )
    image_by_path = {item.relative_path: item for item in manifest.image_files}
    image_evidence = []
    for candidate in result.candidates:
        for source, digest, role in zip(
            candidate.image_paths,
            candidate.image_sha256s,
            candidate.image_roles,
            strict=True,
        ):
            declared = image_by_path[source]
            if declared.sha256 != digest:
                raise ValueError("candidate image evidence does not bind the manifest")
            image_evidence.append({
                "proposed_question_id": candidate.proposed_question_id,
                "relative_path": source,
                "sha256": digest,
                "size_bytes": declared.size_bytes,
                "kind": "image",
                "role": role,
            })
    return {
        "schema": "task12-v122-preflight-v1",
        "batch_id": manifest.batch_id,
        "target_release_version": "V1.22",
        "baseline": _BASELINE,
        "parent_state": {
            "candidate_digest": result.effective_state.candidate_digest,
            "batch_count": len(result.effective_state.batch_ledger),
            "candidate_count": result.effective_state.candidate_count,
            "projected_question_count": result.effective_state.projected_question_count,
        },
        "manifest_policies": {
            name: getattr(manifest, name)
            for name in (
                "schema_version", "project", "module", "chapter", "language_policy",
                "split_policy", "difficulty_policy", "tag_policy", "answer_policy",
                "explanation_policy",
            )
        },
        "candidate_record_order": [item.relative_path for item in manifest.candidate_records],
        "file_evidence": evidence,
        "candidates": [as_plain_dict(item) for item in result.candidates],
        "issues": [as_plain_dict(item) for item in result.issues],
        "duplicate_classifications": [
            {
                "candidate_id": item.proposed_question_id,
                "classification": "new_candidate",
                "reference_question_id": None,
                "evidence": None,
            }
            for item in result.candidates
        ],
        "image_evidence": image_evidence,
        "report": _report_projection(result.report),
    }


def _artifact(path: Path, root: Path, kind: str) -> dict[str, object] | None:
    try:
        if path.is_symlink() or not path.is_file():
            return None
        relative = path.relative_to(root).as_posix()
        relative_path(relative)
        return {
            "relative_path": relative,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "kind": kind,
        }
    except (OSError, InputFormatError, ValueError):
        return None


def _read_json(path: Path) -> tuple[bytes, object] | None:
    if path.is_symlink() or not path.is_file():
        return None
    try:
        raw = path.read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as error:
        raise InputFormatError(
            f"{path.name} cannot establish verification context"
        ) from error
    except OSError:
        return None
    return raw, parsed


def _package_evidence_valid(approved: V122ApprovedBatch) -> bool:
    try:
        root = approved.package_root
        resolved = root.resolve(strict=True)
        if root.is_symlink() or not resolved.is_dir():
            return False
        manifest_path = resolved / "import_manifest.json"
        manifest_read = _read_json(manifest_path)
        if manifest_read is None:
            return False
        _, parsed = manifest_read
        if not _exact_json(parsed, _manifest_projection(approved.preflight_result.manifest)):
            return False
        declared = tuple(
            item
            for name in (
                "candidate_records", "source_files", "answer_files", "image_files",
                "teacher_notes_files", "common_errors_files",
            )
            for item in getattr(approved.preflight_result.manifest, name)
        )
        declared_paths = {item.relative_path for item in declared}
        for item in declared:
            relative_path(item.relative_path)
            path = resolved / item.relative_path
            target = path.resolve(strict=True)
            if (
                path.is_symlink()
                or not target.is_file()
                or not target.is_relative_to(resolved)
                or target.stat().st_size != item.size_bytes
                or sha256_file(target) != item.sha256
            ):
                return False
        actual_paths = set()
        for path in resolved.rglob("*"):
            if path.is_symlink():
                return False
            if path.is_file() and path != manifest_path:
                actual_paths.add(path.relative_to(resolved).as_posix())
        return actual_paths == declared_paths
    except (OSError, PipelineError, RuntimeError, TypeError, ValueError):
        return False


def _candidate_identity(
    approved_batches: tuple[V122ApprovedBatch, ...],
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    ledger: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    images: list[dict[str, object]] = []
    cumulative = 0
    for ordinal, approved in enumerate(approved_batches, start=1):
        result = approved.preflight_result
        approval = approved.approval
        prior = cumulative
        cumulative += len(result.candidates)
        ledger.append({
            "ordinal": ordinal,
            "batch_id": approval.batch_id,
            "parent_candidate_digest": approval.parent_candidate_digest,
            "preflight_sha256": approval.preflight_sha256,
            "manifest_sha256": result.report.manifest_sha256,
            "approval": {
                "batch_id": approval.batch_id,
                "preflight_sha256": approval.preflight_sha256,
                "target_release_version": approval.target_release_version,
                "parent_candidate_digest": approval.parent_candidate_digest,
                "statement": approval.statement,
            },
            "batch_candidate_count": len(result.candidates),
            "cumulative_candidate_count": cumulative,
            "projected_question_count": 591 + cumulative,
        })
        image_by_path = {item.relative_path: item for item in result.manifest.image_files}
        for order, candidate in enumerate(result.candidates):
            destinations = []
            for image_order, (source, digest, role) in enumerate(zip(
                candidate.image_paths,
                candidate.image_sha256s,
                candidate.image_roles,
                strict=True,
            )):
                evidence = image_by_path[source]
                if evidence.sha256 != digest or evidence.kind != "image":
                    raise ValueError("candidate image authority mismatch")
                destination = image_destination("images/sha256", source, digest)
                destinations.append(destination)
                images.append({
                    "batch_ordinal": ordinal,
                    "batch_id": approval.batch_id,
                    "proposed_question_id": candidate.proposed_question_id,
                    "image_order": image_order,
                    "source_relative_path": source,
                    "candidate_relative_path": destination,
                    "sha256": digest,
                    "size_bytes": evidence.size_bytes,
                    "kind": "image",
                    "role": role,
                })
            candidates.append({
                "aggregate_order": 591 + prior + order + 1,
                "batch_ordinal": ordinal,
                "batch_id": approval.batch_id,
                "batch_candidate_order": order,
                "record": as_plain_dict(candidate),
                "candidate_image_paths": destinations,
            })
    images.sort(key=lambda item: (
        item["candidate_relative_path"], item["batch_ordinal"], item["batch_id"],
        item["proposed_question_id"], item["image_order"],
    ))
    counts = {
        "baseline_question_count": 591,
        "batch_count": len(approved_batches),
        "new_candidate_count": cumulative,
        "projected_question_count": 591 + cumulative,
    }
    payload = {
        "schema": "task12-v122-candidate-identity-v1",
        "baseline": _BASELINE,
        "target_release_version": "V1.22",
        "batch_ledger": ledger,
        "candidate_projection": candidates,
        "image_projection": images,
        "counts": counts,
    }
    return payload, ledger, candidates, images


def _authority_expectations(
    approved_batches: tuple[V122ApprovedBatch, ...],
) -> tuple[dict[str, bool], dict[str, bytes], dict[str, object] | None]:
    valid = {
        "parent": True,
        "approval": True,
        "preflight": True,
        "packages": True,
    }
    authority: dict[str, bytes] = {}
    try:
        identity, ledger, _, _ = _candidate_identity(approved_batches)
        prior_ledger: list[dict[str, object]] = []
        prior_candidates: list[dict[str, object]] = []
        prior_images: list[dict[str, object]] = []
        prior_digest = _genesis_digest()
        prior_count = 0
        seen_batch_ids: set[str] = set()
        seen_preflight_sha256s: set[str] = set()
        for ordinal, approved in enumerate(approved_batches, start=1):
            if not _nested_authority_valid(approved):
                raise TypeError
            result = approved.preflight_result
            approval = approved.approval
            expected_statement = (
                f"USER APPROVED IMPORT BATCH {approval.batch_id} "
                f"{approval.preflight_sha256} V1.22 PARENT {approval.parent_candidate_digest}"
            )
            valid["approval"] &= (
                approval.batch_id == result.manifest.batch_id
                and approval.preflight_sha256 == result.report.preflight_sha256
                and approval.target_release_version == "V1.22"
                and approval.parent_candidate_digest == prior_digest
                and approval.statement == expected_statement
                and approval.batch_id not in seen_batch_ids
            )
            valid["parent"] &= (
                result.effective_state.candidate_digest == prior_digest
                and result.effective_state.candidate_count == prior_count
                and result.effective_state.projected_question_count == 591 + prior_count
                and len(result.effective_state.batch_ledger) == ordinal - 1
                and [_plain(item) for item in result.effective_state.batch_ledger]
                == prior_ledger
                and result.report.parent_candidate_digest == prior_digest
                and result.report.parent_batch_count == ordinal - 1
                and result.report.before_count == 591 + prior_count
            )
            payload = _preflight_payload(approved)
            manifest_sha = sha256_bytes(canonical_json_file_bytes(
                _manifest_projection(result.manifest)
            ))
            preflight_sha = sha256_bytes(canonical_json_file_bytes(payload))
            valid["preflight"] &= (
                _preflight_authority_closed(approved)
                and
                result.report.status == "READY FOR USER IMPORT APPROVAL"
                and not result.report.blocking_errors
                and not result.issues
                and result.report.manifest_sha256 == manifest_sha
                and result.report.preflight_sha256 == preflight_sha
                and approval.preflight_sha256 not in seen_preflight_sha256s
            )
            valid["packages"] &= _package_evidence_valid(approved)
            directory = (
                f"authority/batches/{ordinal:06d}/{approval.batch_id}"
            )
            authority[f"{directory}/preflight.json"] = canonical_json_file_bytes({
                "preflight_sha256": approval.preflight_sha256,
                "payload": payload,
            })
            authority[f"{directory}/approval.json"] = canonical_json_file_bytes({
                "schema_version": "task12-v122-import-approval-v1",
                "batch_id": approval.batch_id,
                "preflight_sha256": approval.preflight_sha256,
                "target_release_version": "V1.22",
                "parent_candidate_digest": approval.parent_candidate_digest,
                "statement": approval.statement,
            })
            prior_ledger = ledger[:ordinal]
            prior_candidates = identity["candidate_projection"][: prior_count + len(result.candidates)]
            prior_images = [
                item for item in identity["image_projection"]
                if item["batch_ordinal"] <= ordinal
            ]
            prior_count += len(result.candidates)
            prefix = {
                "schema": "task12-v122-candidate-identity-v1",
                "baseline": _BASELINE,
                "target_release_version": "V1.22",
                "batch_ledger": prior_ledger,
                "candidate_projection": prior_candidates,
                "image_projection": prior_images,
                "counts": {
                    "baseline_question_count": 591,
                    "batch_count": ordinal,
                    "new_candidate_count": prior_count,
                    "projected_question_count": 591 + prior_count,
                },
            }
            prior_digest = sha256_bytes(canonical_json_file_bytes(prefix))
            seen_batch_ids.add(approval.batch_id)
            seen_preflight_sha256s.add(approval.preflight_sha256)
        return valid, authority, identity
    except (
        AttributeError, KeyError, OSError, PipelineError, TypeError, ValueError,
    ):
        return {name: False for name in valid}, authority, None


def _formal_baseline_valid(
    request: V122CandidateVerificationRequest,
    root: Path,
    config: PipelineConfig,
) -> bool:
    try:
        refs = tuple(
            approved.preflight_result.effective_state.baseline_database
            for approved in request.approved_batches
        )
        if not refs or any(type(ref) is not ArtifactRef or ref != refs[0] for ref in refs):
            return False
        reference = refs[0]
        database = reference.path
        release_root = database.parent
        expected_database = (
            config.releases_root
            / "V1.21"
            / "Joy_M2_Complete_Question_DB_V1_21.sqlite3"
        )
        expected_files = {
            "Joy_M2_Complete_Question_DB_V1_21.sqlite3",
            "manifest.json",
            "SHA256SUMS.txt",
            "rollback.json",
        }
        actual_files, actual_directories, regular_tree = _tree_state(release_root)
        if (
            database.absolute() != expected_database.absolute()
            or _has_symlink_component(release_root, config.repo_root)
            or not regular_tree
            or database.is_symlink()
            or not database.is_file()
            or database.resolve(strict=True).is_relative_to(root.resolve(strict=False))
            or reference.kind != "sqlite"
            or reference.sha256 != BASELINE_SHA256
            or reference.size_bytes != BASELINE_SIZE_BYTES
            or database.stat().st_size != BASELINE_SIZE_BYTES
            or sha256_file(database) != BASELINE_SHA256
            or actual_files != expected_files
            or actual_directories
        ):
            return False
        manifest = release_root / "manifest.json"
        raw = manifest.read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
        database_ref = parsed.get("database") if type(parsed) is dict else None
        rollback_ref = parsed.get("rollback") if type(parsed) is dict else None
        database_artifact = {
            "kind": "sqlite",
            "relative_path": "Joy_M2_Complete_Question_DB_V1_21.sqlite3",
            "sha256": BASELINE_SHA256,
            "size_bytes": BASELINE_SIZE_BYTES,
        }
        if (
            type(database_ref) is not dict
            or type(rollback_ref) is not dict
            or database_ref.get("relative_path")
            != "Joy_M2_Complete_Question_DB_V1_21.sqlite3"
            or database_ref.get("sha256") != BASELINE_SHA256
            or database_ref.get("size_bytes") != BASELINE_SIZE_BYTES
            or database_ref.get("kind") != "sqlite"
            or set(rollback_ref) != {"relative_path", "sha256", "size_bytes", "kind"}
            or rollback_ref.get("relative_path") != "rollback.json"
            or not is_sha256(rollback_ref.get("sha256"))
            or type(rollback_ref.get("size_bytes")) is not int
            or rollback_ref.get("size_bytes") < 0
            or rollback_ref.get("kind") != "rollback"
        ):
            return False
        rollback = release_root / "rollback.json"
        expected_sums = (
            f"{BASELINE_SHA256}  Joy_M2_Complete_Question_DB_V1_21.sqlite3\n"
            f"{BASELINE_MANIFEST_SHA256}  manifest.json\n"
            f"{rollback_ref['sha256']}  rollback.json\n"
        ).encode("utf-8")
        sums = (release_root / "SHA256SUMS.txt").read_bytes()
        return (
            len(raw) == BASELINE_MANIFEST_SIZE_BYTES
            and sha256_bytes(raw) == BASELINE_MANIFEST_SHA256
            and type(parsed) is dict
            and parsed.get("release_version") == "V1.21"
            and parsed.get("release_status") == "published"
            and parsed.get("database_schema") == "task11-v121-formal-v1"
            and parsed.get("promotion", {}).get("release_digest") == BASELINE_RELEASE_DIGEST
            and sums == expected_sums
            and rollback.stat().st_size == rollback_ref["size_bytes"]
            and sha256_file(rollback) == rollback_ref["sha256"]
            and _exact_json(
                parsed.get("artifacts"), [database_artifact, rollback_ref]
            )
        )
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _tree_state(root: Path) -> tuple[set[str], set[str], bool]:
    files: set[str] = set()
    directories: set[str] = set()
    valid = True
    try:
        for path in root.rglob("*"):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                valid = False
            elif path.is_dir():
                directories.add(relative)
            elif path.is_file():
                files.add(relative)
            else:
                valid = False
    except OSError:
        valid = False
    return files, directories, valid


def _has_symlink_component(path: Path, base: Path) -> bool:
    del base
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _has_candidate_ancestor(
    path: Path,
    staging_root: Path,
    contract: V122CandidateContract,
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
                and payload.get("release_version") == "V1.22"
                and payload.get("release_status") == "candidate"
            ):
                return True
        current = current.parent
    return False


def _read_sums(path: Path) -> tuple[tuple[str, str], ...] | None:
    if path.is_symlink() or not path.is_file():
        return None
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text or not text.endswith("\n"):
        return None
    result = []
    for line in text.splitlines():
        if len(line) < 67 or line[64:66] != "  " or not is_sha256(line[:64]):
            return None
        try:
            relative = relative_path(line[66:])
        except InputFormatError:
            return None
        result.append((line[:64], relative))
    values = tuple(result)
    canonical = "".join(
        f"{digest}  {relative}\n" for digest, relative in values
    ).encode("utf-8")
    return values if raw == canonical else None


def _sqlite_expected(
    approved_batches: tuple[V122ApprovedBatch, ...],
    candidate_projection: list[dict[str, object]],
    image_projection: list[dict[str, object]],
) -> tuple[tuple, tuple, tuple, tuple]:
    ledgers = []
    candidates = []
    images = []
    taxonomy = []
    cumulative = 0
    candidate_by_key = {
        (item["batch_ordinal"], item["batch_id"], item["batch_candidate_order"]): item
        for item in candidate_projection
    }
    for ordinal, approved in enumerate(approved_batches, start=1):
        result = approved.preflight_result
        approval = approved.approval
        cumulative += len(result.candidates)
        ledgers.append((
            ordinal, approval.batch_id, "V1.22", "task12-v122-candidate-v1",
            approval.parent_candidate_digest, approval.preflight_sha256,
            result.report.manifest_sha256, approval.statement, "V1.21",
            BASELINE_SHA256, BASELINE_RELEASE_DIGEST, 591, len(result.candidates),
            cumulative, 591 + cumulative, "candidate",
        ))
        for order, candidate in enumerate(result.candidates):
            projection = candidate_by_key[(ordinal, approval.batch_id, order)]
            raw = [getattr(candidate, field.name) for field in fields(ImportCandidate)]
            for index in (16, 17, 18, 20):
                raw[index] = canonical_json_bytes(raw[index]).decode("utf-8")
            candidates.append((
                ordinal, approval.batch_id, order, projection["aggregate_order"],
                *raw,
                canonical_json_bytes(projection["candidate_image_paths"]).decode("utf-8"),
                "candidate", 0,
            ))
        primary_types = tuple(sorted({
            candidate.primary_type for candidate in result.candidates
        }))
        tags = tuple(sorted({
            tag for candidate in result.candidates for tag in candidate.tags
        }))
        for kind, values in (("primary_type", primary_types), ("tag", tags)):
            for sort_order, value in enumerate(values, start=1):
                taxonomy.append(
                    (ordinal, approval.batch_id, kind, value, sort_order, "candidate")
                )
    images.extend(tuple(
        item[name] for name in (
            "batch_ordinal", "batch_id", "proposed_question_id", "image_order",
            "source_relative_path", "candidate_relative_path", "sha256", "size_bytes",
            "kind", "role",
        )
    ) for item in image_projection)
    return tuple(ledgers), tuple(candidates), tuple(images), tuple(taxonomy)


def _master(database: sqlite3.Connection) -> dict[str, tuple]:
    return {
        row[1]: row
        for row in database.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        )
    }


def _logical_rows(database: sqlite3.Connection, name: str) -> tuple[tuple, ...]:
    return tuple(sorted(tuple(database.execute(f'SELECT * FROM "{name}"')), key=repr))


def _actual_collision_free(
    database: sqlite3.Connection,
    approved_batches: tuple[V122ApprovedBatch, ...],
) -> bool:
    try:
        baseline_rows = tuple(database.execute(
            "SELECT question_id,source_id,source_question_number,source_section,"
            "source_fragment_hash,normalized_text_sha256,question_text_original,source_image_paths_json,"
            "source_image_sha256s_json,source_image_roles_json "
            "FROM formal_complete_questions_v121 ORDER BY formal_order"
        ))
        candidate_rows = tuple(database.execute(
            "SELECT batch_ordinal,proposed_question_id,source_id,source_question_number,source_section,"
            "source_fragment_hash,normalized_text_sha256,image_paths_json,image_sha256s_json,"
            "image_roles_json FROM task12_v122_candidates_v1 ORDER BY aggregate_order"
        ))
        references = list(baseline_rows)
        ids: set[str] = set()
        locators: dict[tuple[str, str, str], tuple[str, bool, str]] = {}
        fragments: dict[str, tuple[str, bool, str]] = {}
        normalized: set[str] = set()
        image_claims: dict[tuple[str, str], str] = {}
        expected_adaptations: dict[int, list[ImportAdaptation]] = {
            ordinal: []
            for ordinal in range(1, len(approved_batches) + 1)
        }
        for row in references:
            normalized_value = row[5] or _normalized_text_sha256(row[6])
            ids.add(row[0])
            locators[(row[1], row[2], row[3])] = (row[0], True, normalized_value)
            if row[4]:
                fragments[row[4]] = (row[0], True, normalized_value)
            normalized.add(normalized_value)
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
        for row in candidate_rows:
            ordinal = row[0]
            if type(ordinal) is not int or ordinal not in expected_adaptations:
                return False
            locator = (row[2], row[3], row[4])
            locator_reference = locators.get(locator)
            fragment_reference = fragments.get(row[5])
            allowed_adaptation = (
                locator_reference is not None
                and locator_reference == fragment_reference
                and locator_reference[1]
                and row[6] not in normalized
            )
            if allowed_adaptation:
                expected_adaptations[ordinal].append(ImportAdaptation(
                    row[1],
                    locator_reference[0],
                    "adapted",
                    "matched=source_locator+source_fragment_hash;"
                    f"candidate_normalized_text_sha256={row[6]};"
                    f"reference_normalized_text_sha256={locator_reference[2]}",
                    "stable_source_identity_matches_with_transformed_text",
                ))
            if (
                row[1] in ids
                or row[6] in normalized
                or (
                    (locator_reference is not None or fragment_reference is not None)
                    and not allowed_adaptation
                )
            ):
                return False
            for path, digest, role in zip(
                json.loads(row[7]), json.loads(row[8]), json.loads(row[9]), strict=True,
            ):
                prior = image_claims.get((path, role))
                if prior is not None and prior != digest:
                    return False
                image_claims[(path, role)] = digest
            ids.add(row[1])
            locators[locator] = (row[1], False, row[6])
            fragments[row[5]] = (row[1], False, row[6])
            normalized.add(row[6])
        return all(
            tuple(sorted(expected_adaptations[ordinal], key=lambda item: (
                item.candidate_id,
                item.reference_question_id,
                item.adaptation_kind,
                item.evidence,
                item.reason,
            ))) == approved.preflight_result.report.adaptations
            for ordinal, approved in enumerate(approved_batches, start=1)
        )
    except (json.JSONDecodeError, sqlite3.Error, TypeError, ValueError):
        return False


def _sqlite_checks(
    request: V122CandidateVerificationRequest,
    root: Path,
    identity: dict[str, object] | None,
) -> dict[str, bool]:
    state = {
        "sqlite_readability": False,
        "sqlite_integrity": False,
        "sqlite_foreign_keys": False,
        "sqlite_schema": False,
        "v121_preservation": False,
        "batch_ledger": False,
        "candidate_projection": False,
        "effective_collision_closure": False,
        "count_closure": False,
    }
    if identity is None:
        return state
    candidate_path = root / request.contract.database_filename
    baseline_path = request.approved_batches[0].preflight_result.effective_state.baseline_database.path
    if candidate_path.is_symlink() or not candidate_path.is_file():
        return state
    candidate = baseline = None
    try:
        candidate = sqlite3.connect(f"file:{candidate_path}?mode=ro", uri=True)
        baseline = sqlite3.connect(f"file:{baseline_path}?mode=ro", uri=True)
        candidate.execute("PRAGMA foreign_keys=ON")
        candidate.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
        baseline.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
        state["sqlite_readability"] = True
        state["sqlite_integrity"] = candidate.execute(
            "PRAGMA integrity_check"
        ).fetchall() == [("ok",)]
        state["sqlite_foreign_keys"] = candidate.execute(
            "PRAGMA foreign_key_check"
        ).fetchall() == []
        baseline_master = _master(baseline)
        candidate_master = _master(candidate)
        expected_task12 = {}
        for sql in TASK12_SCHEMA_SQL:
            words = sql.split()
            kind = words[1].lower()
            name = words[2]
            expected_task12[name] = (kind, sql)
        actual_task12 = {
            name: row for name, row in candidate_master.items()
            if name.startswith("task12_")
        }
        state["sqlite_schema"] = (
            candidate.execute("PRAGMA user_version").fetchone() == (122,)
            and set(actual_task12) == set(expected_task12)
            and all(
                actual_task12[name][0] == kind
                and normalized_sql(actual_task12[name][3]) == normalized_sql(sql)
                for name, (kind, sql) in expected_task12.items()
            )
            and all(candidate_master.get(name) == row for name, row in baseline_master.items())
            and set(candidate_master) == set(baseline_master) | set(expected_task12)
        )
        preserved_names = tuple(
            name for name, row in baseline_master.items() if row[0] in {"table", "view"}
        )
        state["v121_preservation"] = all(
            _logical_rows(candidate, name) == _logical_rows(baseline, name)
            for name in preserved_names
        )
        expected_rows = _sqlite_expected(
            request.approved_batches,
            identity["candidate_projection"],
            identity["image_projection"],
        )
        actual_ledger = tuple(candidate.execute(
            "SELECT * FROM task12_v122_batch_ledger_v1 ORDER BY batch_ordinal"
        ))
        actual_candidates = tuple(candidate.execute(
            "SELECT * FROM task12_v122_candidates_v1 ORDER BY aggregate_order"
        ))
        actual_images = tuple(candidate.execute(
            "SELECT * FROM task12_v122_images_v1 ORDER BY candidate_relative_path,"
            "batch_ordinal,batch_id,proposed_question_id,image_order"
        ))
        actual_taxonomy = tuple(candidate.execute(
            "SELECT * FROM task12_v122_taxonomy_v1 ORDER BY batch_ordinal,batch_id,"
            "taxonomy_kind,sort_order"
        ))
        state["batch_ledger"] = actual_ledger == expected_rows[0]
        state["candidate_projection"] = (
            actual_candidates == expected_rows[1]
            and actual_images == expected_rows[2]
            and actual_taxonomy == expected_rows[3]
            and tuple(candidate.execute(
                "SELECT * FROM task12_candidate_questions_v122 ORDER BY formal_order"
            ))[:591]
            == tuple(baseline.execute(
                "SELECT * FROM formal_complete_questions_v121 ORDER BY formal_order"
            ))
        )
        state["effective_collision_closure"] = _actual_collision_free(
            candidate, request.approved_batches,
        )
        state["count_closure"] = (
            candidate.execute(
                "SELECT COUNT(*) FROM formal_complete_questions_v121"
            ).fetchone() == (591,)
            and candidate.execute(
                "SELECT COUNT(*) FROM task12_v122_candidates_v1"
            ).fetchone() == (identity["counts"]["new_candidate_count"],)
            and candidate.execute(
                "SELECT COUNT(*) FROM task12_candidate_questions_v122"
            ).fetchone() == (identity["counts"]["projected_question_count"],)
        )
    except (OSError, sqlite3.Error, TypeError, ValueError):
        return state
    finally:
        if candidate is not None:
            candidate.close()
        if baseline is not None:
            baseline.close()
    return state


def _report(checks: dict[str, bool]) -> VerificationReport:
    values = tuple(
        VerificationCheck(name, bool(checks.get(name)), "PASS" if checks.get(name) else "FAIL")
        for name in CHECK_NAMES
    )
    return VerificationReport(
        "PASS" if all(check.passed for check in values) else "FAIL",
        values,
    )


def verify_v122_candidate(
    request: V122CandidateVerificationRequest,
    config: PipelineConfig,
) -> VerificationReport:
    """Verify one V1.22 staging generation without mutating any input."""
    if type(request) is not V122CandidateVerificationRequest:
        raise PipelineError("request must be an exact V122CandidateVerificationRequest")
    if not _reconstructs_exactly(request, V122CandidateVerificationRequest):
        raise PipelineError("verification request carrier is invalid")
    if not _reconstructs_exactly(config, PipelineConfig):
        raise PipelineError("config must be an exact PipelineConfig")
    raw_root = request.candidate_dir
    if not isinstance(raw_root, Path):
        raise PipelineError("candidate_dir must be a Path")
    if not raw_root.exists() and not raw_root.is_symlink():
        raise InputMissingError("candidate directory does not exist")

    configured_staging = config.repo_root / "data" / "staging"
    symlink_root = (
        _has_symlink_component(configured_staging, config.repo_root)
        or _has_symlink_component(raw_root, config.repo_root)
    )
    try:
        root = raw_root.resolve(strict=True)
    except (OSError, RuntimeError):
        return _report({})
    directory_valid = not symlink_root and root.is_dir() and not raw_root.is_symlink()
    if not directory_valid:
        return _report({})

    checks = {name: False for name in CHECK_NAMES}
    checks["candidate_directory"] = True
    checks["candidate_contract"] = (
        type(request.contract) is V122CandidateContract
        and all(
            type(getattr(request.contract, name, None)) is type(expected)
            and getattr(request.contract, name) == expected
            for name, expected in _CONTRACT.items()
        )
    )

    authority_valid, authority_bytes, identity = _authority_expectations(
        request.approved_batches
    )
    try:
        genesis = _genesis_digest()
        first = request.approved_batches[0]
        genesis_bound = (
            genesis == "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7"
            and first.approval.parent_candidate_digest == genesis
            and first.preflight_result.report.parent_candidate_digest == genesis
            and first.preflight_result.effective_state.candidate_digest == genesis
        )
    except (AttributeError, PipelineError, TypeError, ValueError):
        genesis_bound = False
    checks["parent_chain"] = authority_valid["parent"] and genesis_bound
    checks["approval_binding"] = authority_valid["approval"]
    checks["preflight_reconstruction"] = authority_valid["preflight"]
    checks["baseline_authority"] = _formal_baseline_valid(request, root, config)

    manifest_read = _read_json(root / request.contract.manifest_filename)
    rollback_read = _read_json(root / request.contract.rollback_filename)
    authority_reads = {
        relative: _read_json(root / relative) for relative in authority_bytes
    }
    parsed_manifest = manifest_read[1] if manifest_read is not None else None

    authority_files_valid = authority_valid["packages"]
    for relative, expected_bytes in authority_bytes.items():
        read = authority_reads[relative]
        authority_files_valid &= (
            read is not None
            and read[0] == expected_bytes
            and _exact_json(read[1], json.loads(expected_bytes.decode("utf-8")))
        )
    checks["batch_authority_artifacts"] = authority_files_valid

    physical_images: dict[str, dict[str, object]] = {}
    image_projection_valid = identity is not None
    if identity is not None:
        for binding in identity["image_projection"]:
            relative = binding["candidate_relative_path"]
            expected = {
                "relative_path": relative,
                "sha256": binding["sha256"],
                "size_bytes": binding["size_bytes"],
                "kind": "image",
            }
            prior = physical_images.setdefault(relative, expected)
            image_projection_valid &= prior == expected
            artifact = _artifact(root / relative, root, "image")
            image_projection_valid &= artifact == expected

    database_artifact = _artifact(
        root / request.contract.database_filename, root, "sqlite"
    )
    authority_artifacts = [
        _artifact(
            root / relative,
            root,
            "approval" if relative.endswith("approval.json") else "preflight",
        )
        for relative in authority_bytes
    ]
    rollback_artifact = _artifact(
        root / request.contract.rollback_filename, root, "rollback"
    )
    image_artifacts = [physical_images[name] for name in sorted(physical_images)]
    authority_artifacts_sorted = sorted(
        (item for item in authority_artifacts if item is not None),
        key=lambda item: item["relative_path"],
    )
    digest = (
        sha256_bytes(canonical_json_file_bytes(identity)) if identity is not None else None
    )
    counts = identity["counts"] if identity is not None else None
    expected_paths = {
        request.contract.database_filename,
        request.contract.manifest_filename,
        request.contract.sha256s_filename,
        request.contract.rollback_filename,
        *authority_bytes,
        *physical_images,
    }
    expected_rollback = {
        "schema_version": "task12-v122-rollback-v1",
        "action": "delete_unpromoted_v122_candidate_tree_if_digest_matches",
        "candidate_digest": digest,
        "protected_baseline": _BASELINE,
        "candidate_artifacts": sorted(expected_paths),
    }
    checks["rollback_contract"] = (
        rollback_read is not None
        and identity is not None
        and _exact_json(rollback_read[1], expected_rollback)
        and rollback_read[0] == canonical_json_file_bytes(rollback_read[1])
    )
    expected_manifest = {
        "schema_version": "task12-v122-candidate-manifest-v1",
        "release_version": "V1.22",
        "release_status": "candidate",
        "release_model": "append-only-multi-batch-candidate",
        "baseline": _BASELINE,
        "candidate_digest": digest,
        "counts": counts,
        "batch_ledger": identity["batch_ledger"] if identity is not None else None,
        "database": database_artifact,
        "images": image_artifacts,
        "batch_authority_artifacts": authority_artifacts_sorted,
        "rollback": rollback_artifact,
        "verification": {
            "authority": "verify_v122_candidate",
            "check_names": list(CHECK_NAMES),
            "required_status": "PASS",
        },
    }
    checks["candidate_contract"] &= (
        manifest_read is not None
        and database_artifact is not None
        and rollback_artifact is not None
        and len(authority_artifacts_sorted) == len(authority_bytes)
        and _exact_json(parsed_manifest, expected_manifest)
    )
    checks["parent_chain"] &= (
        type(parsed_manifest) is dict
        and identity is not None
        and _exact_json(parsed_manifest.get("batch_ledger"), identity["batch_ledger"])
    )
    checks["approval_binding"] &= checks["batch_authority_artifacts"]
    checks["preflight_reconstruction"] &= checks["batch_authority_artifacts"]

    files, directories, filesystem_types_valid = _tree_state(root)
    expected_directories = {
        parent.as_posix()
        for relative in expected_paths
        for parent in Path(relative).parents
        if parent.as_posix() != "."
    }
    checks["filesystem_closure"] = (
        filesystem_types_valid
        and files == expected_paths
        and directories == expected_directories
    )
    sums = _read_sums(root / request.contract.sha256s_filename)
    expected_sum_paths = tuple(sorted(expected_paths - {request.contract.sha256s_filename}))
    checks["sha256sums_closure"] = sums is not None and (
        tuple(relative for _, relative in sums) == expected_sum_paths
        and len({relative for _, relative in sums}) == len(sums)
        and all(
            _artifact(root / relative, root, "unused") is not None
            and sha256_file(root / relative) == expected_sha
            for expected_sha, relative in sums
        )
    )
    checks["artifact_references"] = (
        type(parsed_manifest) is dict
        and _exact_json(parsed_manifest.get("database"), database_artifact)
        and _exact_json(parsed_manifest.get("rollback"), rollback_artifact)
        and _exact_json(parsed_manifest.get("images"), image_artifacts)
        and _exact_json(
            parsed_manifest.get("batch_authority_artifacts"), authority_artifacts_sorted,
        )
    )
    checks["image_projection"] = image_projection_valid

    checks.update(_sqlite_checks(request, root, identity))
    checks["count_closure"] &= (
        type(parsed_manifest) is dict
        and counts is not None
        and _exact_json(parsed_manifest.get("counts"), counts)
    )
    checks["candidate_digest"] = (
        type(parsed_manifest) is dict
        and digest is not None
        and parsed_manifest.get("candidate_digest") == digest
        and is_sha256(parsed_manifest.get("candidate_digest"))
    )
    checks["deterministic_identity"] = (
        manifest_read is not None
        and manifest_read[0] == canonical_json_file_bytes(manifest_read[1])
        and checks["batch_authority_artifacts"]
        and checks["rollback_contract"]
        and sums is not None
        and tuple(relative for _, relative in sums) == tuple(sorted(relative for _, relative in sums))
    )

    try:
        staging = config.staging_root.resolve(strict=False)
        releases_v122 = (config.releases_root / "V1.22").resolve(strict=False)
        strict_staging = root != staging and root.is_relative_to(staging)
        outside_formal = not root.is_relative_to(releases_v122)
        no_artifact_symlink = filesystem_types_valid
        no_candidate_overlap = all(
            not root.is_relative_to(approved.package_root.resolve(strict=True))
            and not approved.package_root.resolve(strict=True).is_relative_to(root)
            for approved in request.approved_batches
        )
        no_prior_candidate_ancestor = not _has_candidate_ancestor(
            root, staging, request.contract,
        )
        checks["formal_boundary"] = (
            strict_staging
            and outside_formal
            and not symlink_root
            and no_artifact_symlink
            and no_candidate_overlap
            and no_prior_candidate_ancestor
            and checks["baseline_authority"]
        )
    except (OSError, RuntimeError, ValueError):
        checks["formal_boundary"] = False

    return _report(checks)
