"""V1.22 multi-batch import preflight boundary."""

from dataclasses import fields, replace
import hashlib
import json
from pathlib import Path
import sqlite3
import unicodedata

from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError
from joy_m2.ingest.models import (
    ImportAdaptation,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
)
from joy_m2.models import ArtifactRef, VerificationReport

from .v122_models import (
    V122BatchLedgerEntry,
    V122BatchImportManifest,
    V122CandidateContract,
    V122CandidateVerificationRequest,
    V122EffectiveState,
    V122ImportPreflightReport,
    V122ImportPreflightResult,
    V122PreflightRequest,
)
from .v122_verification import verify_v122_candidate


__all__ = ("preflight_v122_import",)

_GENESIS = "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7"
_BASELINE_SHA = "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a"
_BASELINE_SIZE = 10_063_872
_BASELINE_MANIFEST_SHA = "a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40"
_BASELINE_MANIFEST_SIZE = 7_913
_BASELINE_RELEASE_DIGEST = "f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3"
_RAW_FIELDS = {
    "proposed_question_id", "source_id", "source_question_number", "source_section",
    "source_fragment_hash", "question_text_original", "question_text_zh",
    "translation_status", "translation_evidence", "solution_original",
    "solution_verified", "answer_status", "explanation_text", "explanation_status",
    "explanation_evidence", "image_paths", "image_roles", "primary_type", "tags",
    "tag_status", "difficulty_level", "difficulty_status", "enrichment_status",
}
_ISSUE_CODES = {
    "missing_image", "orphan_image", "unsupported_source_format",
    "unknown_primary_type", "unknown_tag", "malformed_candidate_json",
    "invalid_candidate_top_level", "invalid_candidate_record",
    "duplicate_exact", "duplicate_ambiguous", "collision_candidate_id",
    "collision_source_locator", "collision_fragment_sha256",
    "collision_normalized_text_sha256", "collision_image_sha256",
    "file_integrity_mismatch",
}
_FIXED_CONTRACT = {
    "profile": "V1.22", "baseline_release_version": "V1.21",
    "baseline_question_count": 591, "baseline_database_sha256": _BASELINE_SHA,
    "baseline_database_size_bytes": _BASELINE_SIZE,
    "baseline_manifest_sha256": _BASELINE_MANIFEST_SHA,
    "baseline_manifest_size_bytes": _BASELINE_MANIFEST_SIZE,
    "baseline_release_digest": _BASELINE_RELEASE_DIGEST,
    "canonical_manifest_schema": "task12-v122-import-manifest-v1",
    "preflight_schema": "task12-v122-preflight-v1",
    "approval_schema": "task12-v122-import-approval-v1",
    "candidate_manifest_schema": "task12-v122-candidate-manifest-v1",
    "candidate_database_schema": "task12-v122-candidate-v1",
    "candidate_identity_schema": "task12-v122-candidate-identity-v1",
    "rollback_schema": "task12-v122-rollback-v1", "expected_user_version": 122,
    "database_filename": "Joy_M2_V1.22_candidate.sqlite3",
    "manifest_filename": "candidate_manifest.json", "sha256s_filename": "SHA256SUMS",
    "rollback_filename": "rollback.json", "authority_root": "authority/batches",
    "image_root": "images/sha256", "required_baseline_view": "formal_complete_questions_v121",
    "required_candidate_tables": (
        "task12_v122_batch_ledger_v1", "task12_v122_candidates_v1",
        "task12_v122_images_v1", "task12_v122_taxonomy_v1",
    ),
    "required_candidate_views": ("task12_candidate_questions_v122",),
}
_FIXED_MANIFEST = {
    "schema_version": "task12-v122-import-manifest-v1", "project": "Joy M2 AI Database",
    "module": "M2", "target_release_version": "V1.22",
    "language_policy": "preserve_source_and_store_reviewed_chinese_separately",
    "split_policy": "one_complete_question_per_record",
    "difficulty_policy": "joy_level_1_5", "tag_policy": "controlled_primary_type_and_tags",
    "answer_policy": "preserve_source_answer_identity",
    "explanation_policy": "source_or_independently_verified_with_identity",
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _plain(value: object) -> object:
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value)}
    return value


def _file_projection(value: ImportFileEvidence) -> dict[str, object]:
    return {
        "relative_path": value.relative_path, "sha256": value.sha256,
        "size_bytes": value.size_bytes, "kind": value.kind,
    }


def _manifest_projection(manifest: V122BatchImportManifest) -> dict[str, object]:
    groups = {
        name: [_file_projection(item) for item in getattr(manifest, name)]
        for name in (
            "candidate_records", "source_files", "answer_files", "image_files",
            "teacher_notes_files", "common_errors_files",
        )
    }
    return {
        "schema_version": manifest.schema_version, "batch_id": manifest.batch_id,
        "project": manifest.project, "module": manifest.module, "chapter": manifest.chapter,
        "target_release_version": manifest.target_release_version, **groups,
        "language_policy": manifest.language_policy, "split_policy": manifest.split_policy,
        "difficulty_policy": manifest.difficulty_policy, "tag_policy": manifest.tag_policy,
        "answer_policy": manifest.answer_policy, "explanation_policy": manifest.explanation_policy,
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
    except (AttributeError, OSError, PipelineError, RuntimeError, TypeError, ValueError):
        return False
    return reconstructed == value


def _validate_authority(
    request: V122PreflightRequest,
    config: PipelineConfig,
) -> None:
    if not _reconstructs_exactly(request, V122PreflightRequest):
        raise PipelineError("request must be an exact V122PreflightRequest")
    if not _reconstructs_exactly(config, PipelineConfig):
        raise PipelineError("config must be an exact PipelineConfig")
    if not _reconstructs_exactly(request.contract, V122CandidateContract):
        raise PipelineError("contract carrier is invalid")
    if not _reconstructs_exactly(request.manifest, V122BatchImportManifest):
        raise PipelineError("manifest carrier is invalid")
    if not _reconstructs_exactly(request.baseline_database, ArtifactRef):
        raise PipelineError("baseline database carrier is invalid")
    groups = (
        request.manifest.candidate_records,
        request.manifest.source_files,
        request.manifest.answer_files,
        request.manifest.image_files,
        request.manifest.teacher_notes_files,
        request.manifest.common_errors_files,
    )
    if any(
        not _reconstructs_exactly(item, ImportFileEvidence)
        for group in groups
        for item in group
    ):
        raise PipelineError("manifest evidence carrier is invalid")
    for name, expected in _FIXED_CONTRACT.items():
        if type(getattr(request.contract, name)) is not type(expected) or getattr(request.contract, name) != expected:
            raise PipelineError("contract does not match fixed V1.22 authority")
    for name, expected in _FIXED_MANIFEST.items():
        if type(getattr(request.manifest, name)) is not str or getattr(request.manifest, name) != expected:
            raise PipelineError("manifest does not match fixed V1.22 authority")
    baseline = request.baseline_database
    if (
        type(baseline) is not ArtifactRef or baseline.kind != "sqlite"
        or baseline.sha256 != _BASELINE_SHA or baseline.size_bytes != _BASELINE_SIZE
    ):
        raise PipelineError("baseline database does not match fixed V1.21 authority")
    manifest_path = baseline.path.parent / "manifest.json"
    try:
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise PipelineError("baseline sibling manifest must be a regular file")
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise PipelineError("baseline sibling manifest cannot be read") from exc
    if (
        len(manifest_bytes) != _BASELINE_MANIFEST_SIZE
        or _sha(manifest_bytes) != _BASELINE_MANIFEST_SHA
    ):
        raise PipelineError("baseline sibling manifest does not match fixed V1.21 authority")
    if (
        request.parent_candidate is not None
        and request.parent_candidate.contract != request.contract
    ):
        raise PipelineError("parent candidate contract does not match preflight authority")


def _object_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = tuple(key for key, _ in pairs)
    if len(keys) != len(set(keys)):
        raise PipelineError("canonical V1.22 JSON contains duplicate keys")
    return dict(pairs)


def _manifest_from_package(root: Path) -> dict[str, object]:
    path = root / "import_manifest.json"
    try:
        payload = json.loads(
            path.read_bytes().decode("utf-8"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except PipelineError:
        raise
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise PipelineError("canonical V1.22 manifest must be strict UTF-8 JSON") from exc
    expected = tuple(field.name for field in fields(V122BatchImportManifest))
    if type(payload) is not dict or tuple(payload) != expected:
        raise PipelineError("canonical V1.22 manifest has the wrong field envelope")
    return payload


def _same_json_types_and_values(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(actual) is dict:
        if tuple(actual) != tuple(expected):
            return False
        return all(
            _same_json_types_and_values(actual[name], expected[name])
            for name in actual
        )
    if type(actual) is list:
        return len(actual) == len(expected) and all(
            _same_json_types_and_values(left, right)
            for left, right in zip(actual, expected, strict=True)
        )
    return actual == expected


def _load_package(
    manifest: V122BatchImportManifest, root: Path,
) -> tuple[
    dict[str, bytes],
    tuple[ImportFileEvidence, ...],
    tuple[ImportIssue, ...],
    frozenset[str],
]:
    try:
        resolved_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise PipelineError("package_root cannot be resolved") from exc
    if root.is_symlink() or not resolved_root.is_dir():
        raise PipelineError("package_root must be a regular directory")
    manifest_payload = _manifest_from_package(resolved_root)
    if not _same_json_types_and_values(
        manifest_payload, _manifest_projection(manifest)
    ):
        raise PipelineError("request manifest differs from canonical package manifest")
    declared = tuple(
        item
        for name in (
            "candidate_records", "source_files", "answer_files", "image_files",
            "teacher_notes_files", "common_errors_files",
        )
        for item in getattr(manifest, name)
    )
    content: dict[str, bytes] = {}
    issues: list[ImportIssue] = []
    untrusted_paths: set[str] = set()
    for evidence in declared:
        path = root / evidence.relative_path
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(resolved_root)
            if path.is_symlink() or not resolved.is_file():
                raise PipelineError("declared package path is unsafe")
            data = resolved.read_bytes()
        except PipelineError:
            raise
        except (OSError, RuntimeError, ValueError) as exc:
            raise PipelineError("declared package file cannot be read safely") from exc
        actual_sha256 = _sha(data)
        if len(data) != evidence.size_bytes or actual_sha256 != evidence.sha256:
            untrusted_paths.add(evidence.relative_path)
            issues.append(_issue(
                "file_integrity_mismatch", None, "file_integrity", {
                    "relative_path": evidence.relative_path,
                    "expected_sha256": evidence.sha256,
                    "actual_sha256": actual_sha256,
                    "expected_size_bytes": evidence.size_bytes,
                    "actual_size_bytes": len(data),
                },
            ))
            continue
        content[evidence.relative_path] = data
    actual: set[str] = set()
    for path in resolved_root.rglob("*"):
        if path.is_symlink():
            raise PipelineError("package symlinks are forbidden")
        if path.is_file() and path != resolved_root / "import_manifest.json":
            actual.add(path.relative_to(resolved_root).as_posix())
    if actual != {item.relative_path for item in declared}:
        raise PipelineError("package inventory differs from manifest")
    return (
        content,
        tuple(sorted(declared, key=lambda item: item.relative_path)),
        tuple(sorted(issues, key=lambda item: (
            item.proposed_question_id or "", item.code, item.field, item.evidence,
        ))),
        frozenset(untrusted_paths),
    )


def _normalize(value: str) -> str:
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
    return "\n".join(lines)


def _depends_on_untrusted(record: object, untrusted_paths: frozenset[str]) -> bool:
    if type(record) is not dict:
        return False
    image_paths = record.get("image_paths")
    if type(image_paths) is list and any(
        type(path) is str and path in untrusted_paths for path in image_paths
    ):
        return True
    for status_name, evidence_name in (
        ("translation_status", "translation_evidence"),
        ("explanation_status", "explanation_evidence"),
    ):
        evidence = record.get(evidence_name)
        if (
            record.get(status_name) == "source_present"
            and type(evidence) is str
            and evidence.startswith("source:")
            and "#" in evidence[7:]
            and evidence[7:].split("#", 1)[0] in untrusted_paths
        ):
            return True
    return False


def _load_candidates(
    manifest: V122BatchImportManifest,
    content: dict[str, bytes],
    untrusted_paths: frozenset[str],
    initial_issues: tuple[ImportIssue, ...],
) -> tuple[
    tuple[ImportCandidate, ...],
    tuple[dict[str, object], ...],
    tuple[ImportIssue, ...],
    tuple[str, ...],
]:
    image_files = {
        item.relative_path: item
        for item in manifest.image_files
        if item.relative_path not in untrusted_paths
    }
    source_paths = {
        item.relative_path
        for item in manifest.source_files
        if item.relative_path not in untrusted_paths
    }
    candidates: list[ImportCandidate] = []
    image_evidence: list[dict[str, object]] = []
    issues = list(initial_issues)
    missing_image_paths: list[str] = []
    for evidence in manifest.candidate_records:
        if evidence.relative_path in untrusted_paths:
            continue
        try:
            records = json.loads(content[evidence.relative_path].decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            issues.append(_issue(
                "malformed_candidate_json", None, "candidate_records",
                {"relative_path": evidence.relative_path},
            ))
            continue
        if type(records) is not list:
            issues.append(_issue(
                "invalid_candidate_top_level", None, "candidate_records",
                {"relative_path": evidence.relative_path, "expected": "array"},
            ))
            continue
        for record_index, record in enumerate(records):
            if _depends_on_untrusted(record, untrusted_paths):
                continue
            try:
                if type(record) is not dict or set(record) != _RAW_FIELDS:
                    raise PipelineError("candidate record must have exact fields")
                if (
                    type(record["image_paths"]) is not list
                    or type(record["image_roles"]) is not list
                    or type(record["tags"]) is not list
                ):
                    raise PipelineError("candidate tuple fields must be arrays")
                paths = tuple(record["image_paths"])
                roles = tuple(record["image_roles"])
                if (
                    len(paths) != len(roles)
                    or any(type(path) is not str for path in paths)
                    or any(type(role) is not str for role in roles)
                ):
                    raise PipelineError("candidate image bindings are invalid")
                for status_name, evidence_name in (
                    ("translation_status", "translation_evidence"),
                    ("explanation_status", "explanation_evidence"),
                ):
                    source = record[evidence_name]
                    if record[status_name] == "source_present":
                        if (
                            type(source) is not str
                            or not source.startswith("source:")
                            or "#" not in source[7:]
                            or source[7:].split("#", 1)[0] not in source_paths
                        ):
                            raise PipelineError("source-present evidence is invalid")
                candidate = ImportCandidate(
                    proposed_question_id=record["proposed_question_id"],
                    source_id=record["source_id"],
                    source_question_number=record["source_question_number"],
                    source_section=record["source_section"],
                    source_fragment_hash=record["source_fragment_hash"],
                    normalized_text_sha256=_sha(_normalize(record["question_text_original"]).encode("utf-8")),
                    question_text_original=record["question_text_original"],
                    question_text_zh=record["question_text_zh"],
                    translation_status=record["translation_status"],
                    translation_evidence=record["translation_evidence"],
                    solution_original=record["solution_original"],
                    solution_verified=record["solution_verified"],
                    answer_status=record["answer_status"],
                    explanation_text=record["explanation_text"],
                    explanation_status=record["explanation_status"],
                    explanation_evidence=record["explanation_evidence"],
                    image_paths=paths,
                    image_sha256s=tuple("0" * 64 for _ in paths),
                    image_roles=roles,
                    primary_type=record["primary_type"],
                    tags=tuple(record["tags"]),
                    tag_status=record["tag_status"],
                    difficulty_level=record["difficulty_level"],
                    difficulty_status=record["difficulty_status"],
                    enrichment_status=record["enrichment_status"],
                )
                missing = tuple(
                    (path, role)
                    for path, role in zip(paths, roles, strict=True)
                    if path not in image_files
                )
                if missing:
                    for path, role in missing:
                        missing_image_paths.append(path)
                        issues.append(_issue(
                            "missing_image", None, "images", {
                                "candidate_id": candidate.proposed_question_id,
                                "relative_path": path,
                                "role": role,
                            },
                        ))
                    continue
                candidate = replace(
                    candidate,
                    image_sha256s=tuple(image_files[path].sha256 for path in paths),
                )
            except (KeyError, TypeError, PipelineError):
                issues.append(_issue(
                    "invalid_candidate_record", None, "candidate_records", {
                        "relative_path": evidence.relative_path,
                        "record_index": record_index,
                    },
                ))
                continue
            candidates.append(candidate)
            for path, digest, role in zip(paths, candidate.image_sha256s, roles, strict=True):
                item = image_files[path]
                image_evidence.append({
                    "proposed_question_id": candidate.proposed_question_id,
                    "relative_path": path, "sha256": digest, "size_bytes": item.size_bytes,
                    "kind": "image", "role": role,
                })
    bound_images = {path for candidate in candidates for path in candidate.image_paths}
    for relative_path in sorted(set(image_files) - bound_images):
        item = image_files[relative_path]
        issues.append(_issue(
            "orphan_image", None, "images", {
                "relative_path": relative_path,
                "sha256": item.sha256,
            },
        ))
    for name in (
        "candidate_records", "source_files", "answer_files", "image_files",
        "teacher_notes_files", "common_errors_files",
    ):
        for item in getattr(manifest, name):
            lower = item.relative_path.lower()
            for suffix, source_format in (
                (".mmd.zip", "mmd_zip"), (".mmd", "mmd"), (".pdf", "pdf"),
            ):
                if lower.endswith(suffix):
                    issues.append(_issue(
                        "unsupported_source_format", None, "source_format", {
                            "relative_path": item.relative_path,
                            "format": source_format,
                        },
                    ))
                    break
    return (
        tuple(candidates),
        tuple(image_evidence),
        tuple(sorted(issues, key=lambda item: (
            item.proposed_question_id or "", item.code, item.field, item.evidence,
        ))),
        tuple(missing_image_paths),
    )


def _parse_array(value: object, name: str) -> tuple[object, ...]:
    if value is None:
        return ()
    if type(value) is not str:
        raise PipelineError(f"formal {name} is invalid")
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise PipelineError(f"formal {name} is invalid") from exc
    if type(decoded) is not list:
        raise PipelineError(f"formal {name} must be an array")
    return tuple(decoded)


def _formal_indexes(path: Path) -> tuple[dict[str, object], frozenset[str], frozenset[str]]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise PipelineError("baseline database cannot be read") from exc
    if len(data) != _BASELINE_SIZE or _sha(data) != _BASELINE_SHA:
        raise PipelineError("baseline database bytes do not match V1.21")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{path.resolve(strict=True).as_uri()}?mode=ro", uri=True)
        if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise PipelineError("baseline integrity check failed")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise PipelineError("baseline foreign-key check failed")
        metadata = dict(connection.execute(
            "SELECT key,value FROM release_metadata_v2 WHERE key IN ('release_version','schema_version')"
        ))
        if metadata != {"release_version": "V1.21", "schema_version": "task11-v121-formal-v1"}:
            raise PipelineError("baseline metadata does not match V1.21")
        rows = connection.execute(
            "SELECT formal_order,question_id,source_id,source_question_number,source_section,"
            "source_fragment_hash,normalized_text_sha256,question_text_original,"
            "source_image_paths_json,source_image_sha256s_json,source_image_roles_json,"
            "primary_type,tags_json FROM formal_complete_questions_v121 ORDER BY formal_order"
        ).fetchall()
        if len(rows) != 591 or tuple(row[0] for row in rows) != tuple(range(1, 592)):
            raise PipelineError("formal V1.21 view must contain exact rows 1..591")
        references: dict[str, dict[str, object]] = {}
        locator_index: dict[object, list[str]] = {}
        fragment_index: dict[object, list[str]] = {}
        normalized_index: dict[object, list[str]] = {}
        image_binding_index: dict[object, list[str]] = {}
        image_identity_index: dict[object, list[str]] = {}
        primary_types: set[str] = set()
        tags: set[str] = set()
        for row in rows:
            paths = _parse_array(row[8], "image paths")
            digests = _parse_array(row[9], "image digests")
            roles = _parse_array(row[10], "image roles")
            if all(type(item) is dict for item in paths):
                try:
                    images = tuple(
                        (item["path"], item["role"], item["sha256"])
                        for item in paths
                        if set(item) == {"path", "role", "sha256"}
                    )
                except (KeyError, TypeError) as exc:
                    raise PipelineError("formal image identity is invalid") from exc
                if len(images) != len(paths):
                    raise PipelineError("formal image identity is invalid")
            elif all(type(item) is str for item in paths):
                images = tuple(zip(paths, roles, digests, strict=True)) if digests or roles else tuple(
                    (item, None, None) for item in paths
                )
            else:
                raise PipelineError("formal image identity is invalid")
            reference = {
                "question_id": row[1], "locator": (row[2], row[3], row[4]),
                "fragment": row[5], "normalized": row[6] or _sha(_normalize(row[7]).encode("utf-8")),
                "images": images, "baseline": True,
            }
            references[row[1]] = reference
            locator_index.setdefault(reference["locator"], []).append(row[1])
            fragment_index.setdefault(reference["fragment"], []).append(row[1])
            normalized_index.setdefault(reference["normalized"], []).append(row[1])
            for image_path, role, digest in images:
                if role is None or digest is None:
                    continue
                image_binding_index.setdefault((image_path, role), []).append(row[1])
                image_identity_index.setdefault((image_path, role, digest), []).append(row[1])
            primary_types.add(row[11])
            tags.update(_parse_array(row[12], "tags"))
        if len(references) != 591:
            raise PipelineError("formal V1.21 question IDs must be unique")
        indexes = {
            "references": references,
            "question_id": {question_id: (question_id,) for question_id in references},
            "source_locator": {
                key: tuple(sorted(values)) for key, values in locator_index.items()
            },
            "source_fragment_sha256": {
                key: tuple(sorted(values)) for key, values in fragment_index.items()
            },
            "normalized_text_sha256": {
                key: tuple(sorted(values)) for key, values in normalized_index.items()
            },
            "image_binding": {
                key: tuple(sorted(values)) for key, values in image_binding_index.items()
            },
            "image_identity": {
                key: tuple(sorted(values)) for key, values in image_identity_index.items()
            },
        }
        return indexes, frozenset(primary_types), frozenset(tags)
    except PipelineError:
        raise
    except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
        raise PipelineError("baseline database cannot be validated read-only") from exc
    finally:
        if connection is not None:
            connection.close()


def _ledger_entry(
    ordinal: int,
    approved: object,
    cumulative: int,
) -> V122BatchLedgerEntry:
    result = approved.preflight_result
    approval = approved.approval
    return V122BatchLedgerEntry(
        ordinal,
        approval.batch_id,
        approval.parent_candidate_digest,
        approval.preflight_sha256,
        result.report.manifest_sha256,
        approval,
        len(result.candidates),
        cumulative,
        591 + cumulative,
    )


def _parent_context(
    request: V122PreflightRequest,
    config: PipelineConfig,
    indexes: dict[str, object],
    primary_types: frozenset[str],
    tags: frozenset[str],
) -> tuple[V122EffectiveState, dict[str, object], frozenset[str], frozenset[str]]:
    parent = request.parent_candidate
    if parent is None:
        return (
            V122EffectiveState(request.baseline_database, _GENESIS, (), 0, 591),
            indexes,
            primary_types,
            tags,
        )
    raise NotImplementedError("V1.22 verified-parent preflight pending Task 4B1")


def _evidence(value: dict[str, object]) -> str:
    return _canonical(value).decode("utf-8")


def _issue(
    code: str,
    candidate: ImportCandidate | str | None,
    field: str,
    evidence: dict[str, object],
) -> ImportIssue:
    if code not in _ISSUE_CODES:
        raise PipelineError("unapproved V1.22 issue code")
    candidate_id = (
        candidate.proposed_question_id
        if type(candidate) is ImportCandidate
        else candidate
    )
    return ImportIssue(code, "blocking", candidate_id, field, _evidence(evidence))


def _candidate_reference(candidate: ImportCandidate) -> dict[str, object]:
    return {
        "question_id": candidate.proposed_question_id,
        "locator": (
            candidate.source_id,
            candidate.source_question_number,
            candidate.source_section,
        ),
        "fragment": candidate.source_fragment_hash,
        "normalized": candidate.normalized_text_sha256,
        "images": tuple(zip(
            candidate.image_paths,
            candidate.image_roles,
            candidate.image_sha256s,
            strict=True,
        )),
        "baseline": False,
    }


def _candidate_images(candidate: ImportCandidate) -> tuple[tuple[str, str, str], ...]:
    return tuple(zip(
        candidate.image_paths,
        candidate.image_roles,
        candidate.image_sha256s,
        strict=True,
    ))


def _is_exact_duplicate(
    candidate: ImportCandidate,
    reference: dict[str, object],
) -> bool:
    return (bool(reference["baseline"]) or bool(reference.get("accepted"))) and (
        (
            candidate.source_id,
            candidate.source_question_number,
            candidate.source_section,
        )
        == reference["locator"]
        and candidate.source_fragment_hash == reference["fragment"]
        and candidate.normalized_text_sha256 == reference["normalized"]
        and _candidate_images(candidate) == reference["images"]
    )


def _image_collision_issues(
    candidate: ImportCandidate,
    reference: dict[str, object],
) -> tuple[ImportIssue, ...]:
    issues: list[ImportIssue] = []
    reference_bindings = {
        (path, role): digest
        for path, role, digest in reference["images"]
        if role is not None and digest is not None
    }
    for path, role, digest in _candidate_images(candidate):
        reference_digest = reference_bindings.get((path, role))
        if reference_digest is None or reference_digest == digest:
            continue
        issues.append(_issue(
            "collision_image_sha256", candidate, "image_sha256s", {
                "candidate_id": candidate.proposed_question_id,
                "candidate_image_path": path,
                "candidate_image_role": role,
                "candidate_image_sha256": digest,
                "reference_question_id": reference["question_id"],
                "reference_image_path": path,
                "reference_image_role": role,
                "reference_image_sha256": reference_digest,
            },
        ))
    return tuple(issues)


def _collision_issues(
    candidate: ImportCandidate,
    reference: dict[str, object],
    signals: frozenset[str],
) -> tuple[ImportIssue, ...]:
    issues: list[ImportIssue] = []
    locator = (
        candidate.source_id,
        candidate.source_question_number,
        candidate.source_section,
    )
    if "candidate_id" in signals:
        issues.append(_issue(
            "collision_candidate_id", candidate, "proposed_question_id", {
                "candidate_id": candidate.proposed_question_id,
                "reference_question_id": reference["question_id"],
                "candidate_fragment_sha256": candidate.source_fragment_hash,
                "reference_fragment_sha256": reference["fragment"],
            },
        ))
    if "source_locator" in signals and (
        candidate.source_fragment_hash != reference["fragment"]
        or candidate.normalized_text_sha256 != reference["normalized"]
        or _candidate_images(candidate) != reference["images"]
    ):
        issues.append(_issue(
            "collision_source_locator", candidate, "source_locator", {
                "candidate_id": candidate.proposed_question_id,
                "candidate_source_locator": locator,
                "candidate_fragment_sha256": candidate.source_fragment_hash,
                "reference_question_id": reference["question_id"],
                "reference_source_locator": reference["locator"],
                "reference_fragment_sha256": reference["fragment"],
            },
        ))
    if "source_fragment_sha256" in signals:
        issues.append(_issue(
            "collision_fragment_sha256", candidate, "source_fragment_hash", {
                "candidate_id": candidate.proposed_question_id,
                "candidate_source_locator": locator,
                "reference_question_id": reference["question_id"],
                "reference_source_locator": reference["locator"],
                "source_fragment_sha256": candidate.source_fragment_hash,
            },
        ))
    if "normalized_text_sha256" in signals:
        issues.append(_issue(
            "collision_normalized_text_sha256", candidate,
            "normalized_text_sha256", {
                "candidate_id": candidate.proposed_question_id,
                "reference_question_id": reference["question_id"],
                "normalized_text_sha256": candidate.normalized_text_sha256,
            },
        ))
    issues.extend(_image_collision_issues(candidate, reference))
    return tuple(issues)


def _classify(
    candidates: tuple[ImportCandidate, ...],
    indexes: dict[str, object],
    initial_issues: tuple[ImportIssue, ...],
    primary_types: frozenset[str],
    tags: frozenset[str],
) -> tuple[tuple[ImportIssue, ...], tuple[ImportAdaptation, ...], tuple[dict[str, object], ...]]:
    issues: list[ImportIssue] = list(initial_issues)
    adaptations: list[ImportAdaptation] = []
    classifications: list[dict[str, object]] = []
    references: dict[str, dict[str, object]] = indexes["references"]
    prior_candidates: dict[str, ImportCandidate] = {}
    primary_types = primary_types | {"代数"}
    tags = tags | {"一元一次方程"}
    for candidate in candidates:
        locator = (candidate.source_id, candidate.source_question_number, candidate.source_section)
        images = _candidate_images(candidate)
        match_references = dict(references)
        matches: dict[str, set[str]] = {}

        def add_matches(index_name: str, key: object, signal: str) -> None:
            for reference_id in indexes[index_name].get(key, ()):
                matches.setdefault(reference_id, set()).add(signal)

        add_matches("question_id", candidate.proposed_question_id, "candidate_id")
        add_matches("source_locator", locator, "source_locator")
        add_matches(
            "source_fragment_sha256", candidate.source_fragment_hash,
            "source_fragment_sha256",
        )
        add_matches(
            "normalized_text_sha256", candidate.normalized_text_sha256,
            "normalized_text_sha256",
        )
        for path, role, digest in images:
            add_matches("image_binding", (path, role), "image_sha256")
            add_matches("image_identity", (path, role, digest), "image_sha256")
        prior = prior_candidates.get(candidate.proposed_question_id)
        if prior is not None:
            reference_id = prior.proposed_question_id
            match_references.setdefault(reference_id, _candidate_reference(prior))
            matches.setdefault(reference_id, set()).add("candidate_id")
        exact = [
            reference_id
            for reference_id in sorted(matches)
            if _is_exact_duplicate(candidate, match_references[reference_id])
        ]
        candidate_issues: list[ImportIssue] = []
        if candidate.primary_type not in primary_types:
            candidate_issues.append(_issue(
                "unknown_primary_type", candidate, "primary_type", {
                    "candidate_id": candidate.proposed_question_id,
                    "value": candidate.primary_type,
                },
            ))
        unknown_tags = tuple(sorted(set(candidate.tags) - tags))
        if unknown_tags:
            candidate_issues.append(_issue(
                "unknown_tag", candidate, "tags", {
                    "candidate_id": candidate.proposed_question_id,
                    "unknown_tags": unknown_tags,
                },
            ))
        ambiguous_issue: ImportIssue | None = None
        exact_issue: ImportIssue | None = None
        if len(exact) > 1 or (not exact and len(matches) > 1):
            ambiguous_issue = _issue("duplicate_ambiguous", candidate, "duplicate", {
                "candidate_id": candidate.proposed_question_id,
                "matches": [
                    {"reference_question_id": key, "signals": sorted(matches[key])}
                    for key in sorted(matches)
                ],
            })
            candidate_issues.append(ambiguous_issue)
        elif exact:
            reference_id = exact[0]
            exact_issue = _issue("duplicate_exact", candidate, "candidate", {
                "candidate_id": candidate.proposed_question_id,
                "reference_question_id": reference_id,
                "normalized_text_sha256": candidate.normalized_text_sha256,
            })
            candidate_issues.append(exact_issue)
            for other_reference_id in sorted(matches):
                if other_reference_id == reference_id:
                    continue
                candidate_issues.extend(_collision_issues(
                    candidate,
                    match_references[other_reference_id],
                    frozenset(matches[other_reference_id]),
                ))
        elif len(matches) == 1:
            reference_id = next(iter(matches))
            reference = match_references[reference_id]
            signals = frozenset(matches[reference_id])
            if (
                bool(reference["baseline"])
                and locator == reference["locator"]
                and candidate.source_fragment_hash == reference["fragment"]
                and candidate.normalized_text_sha256 != reference["normalized"]
                and "candidate_id" not in signals
            ):
                adaptations.append(ImportAdaptation(
                    candidate.proposed_question_id, reference_id, "adapted",
                    "matched=source_locator+source_fragment_hash;"
                    f"candidate_normalized_text_sha256={candidate.normalized_text_sha256};"
                    f"reference_normalized_text_sha256={reference['normalized']}",
                    "stable_source_identity_matches_with_transformed_text",
                ))
                candidate_issues.extend(_image_collision_issues(candidate, reference))
            else:
                candidate_issues.extend(_collision_issues(
                    candidate, reference, signals,
                ))
        candidate_issues.sort(key=lambda item: (
            item.proposed_question_id or "", item.code, item.field, item.evidence,
        ))
        issues.extend(candidate_issues)
        independent_blockers = [
            item for item in candidate_issues if item.code != "duplicate_exact"
        ]
        if ambiguous_issue is not None:
            classification, reference_id = "rejected", None
            classification_issue = ambiguous_issue
        elif exact_issue is not None:
            classification = "rejected" if independent_blockers else "duplicate"
            reference_id = exact[0]
            classification_issue = exact_issue
        elif independent_blockers:
            classification_issue = independent_blockers[0]
            classification, reference_id = (
                "rejected",
                json.loads(classification_issue.evidence).get("reference_question_id"),
            )
        else:
            classification, reference_id = "new_candidate", None
            classification_issue = None
        classifications.append({
            "candidate_id": candidate.proposed_question_id, "classification": classification,
            "reference_question_id": reference_id,
            "evidence": None if classification_issue is None else classification_issue.evidence,
        })
        prior_candidates.setdefault(candidate.proposed_question_id, candidate)
    return (
        tuple(sorted(issues, key=lambda item: (item.proposed_question_id or "", item.code, item.field, item.evidence))),
        tuple(sorted(adaptations, key=lambda item: (
            item.candidate_id, item.reference_question_id, item.adaptation_kind, item.evidence, item.reason,
        ))),
        tuple(classifications),
    )


def _report_values(
    manifest: V122BatchImportManifest, candidates: tuple[ImportCandidate, ...],
    issues: tuple[ImportIssue, ...], adaptations: tuple[ImportAdaptation, ...],
    classifications: tuple[dict[str, object], ...], files: tuple[ImportFileEvidence, ...],
    missing_image_paths: tuple[str, ...], state: V122EffectiveState,
) -> dict[str, object]:
    counts = {name: sum(item["classification"] == name for item in classifications) for name in (
        "new_candidate", "duplicate", "rejected",
    )}
    ambiguous_evidence = frozenset(
        item.evidence for item in issues if item.code == "duplicate_ambiguous"
    )
    ambiguous_occurrences = tuple(
        item["classification"] == "rejected"
        and item["reference_question_id"] is None
        and item["evidence"] in ambiguous_evidence
        for item in classifications
    )
    level_counts = tuple(
        (level, sum(candidate.difficulty_level == level for candidate in candidates))
        for level in range(1, 6) if any(candidate.difficulty_level == level for candidate in candidates)
    )
    blocking = tuple(item.code for item in issues if item.severity == "blocking")

    def issue_paths(code: str) -> tuple[str, ...]:
        return tuple(
            json.loads(item.evidence)["relative_path"]
            for item in issues
            if item.code == code
        )

    return {
        "batch_id": manifest.batch_id,
        "status": "BLOCKED — IMPORT PREFLIGHT FAILED" if blocking else "READY FOR USER IMPORT APPROVAL",
        "manifest_sha256": _sha(_canonical(_manifest_projection(manifest)) + b"\n"),
        "baseline_version": "V1.21", "baseline_release_digest": _BASELINE_RELEASE_DIGEST,
        "baseline_question_count": 591, "target_release_version": "V1.22",
        "parent_candidate_digest": state.candidate_digest,
        "parent_batch_count": len(state.batch_ledger),
        "before_count": state.projected_question_count,
        "detected_count": len(candidates), "new_candidate_count": counts["new_candidate"],
        "duplicate_count": counts["duplicate"], "rejected_count": counts["rejected"],
        "ambiguous_count": sum(ambiguous_occurrences),
        "approved_count": 0,
        "projected_after_count": state.projected_question_count + counts["new_candidate"],
        "readable_files": tuple(item.relative_path for item in files), "unreadable_files": (),
        "unsupported_files": tuple(sorted(issue_paths("unsupported_source_format"))),
        "teacher_notes_file_count": len(manifest.teacher_notes_files),
        "common_errors_file_count": len(manifest.common_errors_files),
        "ambiguous_splits": tuple(
            candidate.proposed_question_id
            for candidate, is_ambiguous in zip(candidates, ambiguous_occurrences, strict=True)
            if is_ambiguous
        ),
        "missing_answers": tuple(c.proposed_question_id for c in candidates if c.answer_status == "missing_from_source"),
        "missing_explanations": tuple(c.proposed_question_id for c in candidates if c.explanation_status == "missing"),
        "incomplete_enrichments": tuple(c.proposed_question_id for c in candidates if c.enrichment_status == "incomplete"),
        "missing_images": missing_image_paths,
        "orphan_images": tuple(sorted(issue_paths("orphan_image"))),
        "level_counts": level_counts,
        "proposed_ids": tuple(c.proposed_question_id for c in candidates), "adaptations": adaptations,
        "warnings": (), "blocking_errors": blocking,
    }


def _preflight_payload(
    request: V122PreflightRequest, candidates: tuple[ImportCandidate, ...],
    issues: tuple[ImportIssue, ...], classifications: tuple[dict[str, object], ...],
    image_evidence: tuple[dict[str, object], ...], files: tuple[ImportFileEvidence, ...],
    report: dict[str, object], state: V122EffectiveState,
) -> dict[str, object]:
    manifest = request.manifest
    return {
        "schema": "task12-v122-preflight-v1", "batch_id": manifest.batch_id,
        "target_release_version": "V1.22",
        "baseline": {
            "release_version": "V1.21", "question_count": 591,
            "database_schema": "task11-v121-formal-v1",
            "sqlite": {"sha256": _BASELINE_SHA, "size_bytes": _BASELINE_SIZE, "kind": "sqlite"},
            "manifest": {"sha256": _BASELINE_MANIFEST_SHA, "size_bytes": _BASELINE_MANIFEST_SIZE, "kind": "manifest"},
            "release_digest": _BASELINE_RELEASE_DIGEST,
        },
        "parent_state": {
            "candidate_digest": state.candidate_digest,
            "batch_count": len(state.batch_ledger),
            "candidate_count": state.candidate_count,
            "projected_question_count": state.projected_question_count,
        },
        "manifest_policies": {
            name: getattr(manifest, name) for name in (
                "schema_version", "project", "module", "chapter", "language_policy",
                "split_policy", "difficulty_policy", "tag_policy", "answer_policy",
                "explanation_policy",
            )
        },
        "candidate_record_order": [item.relative_path for item in manifest.candidate_records],
        "file_evidence": [_file_projection(item) for item in files],
        "candidates": [_plain(item) for item in candidates],
        "issues": [_plain(item) for item in issues],
        "duplicate_classifications": list(classifications),
        "image_evidence": list(image_evidence),
        "report": {name: _plain(value) for name, value in report.items()},
    }


def preflight_v122_import(
    request: V122PreflightRequest,
    config: PipelineConfig,
) -> V122ImportPreflightResult:
    """Validate one canonical package against formal V1.21 without writing."""
    if type(config) is not PipelineConfig:
        raise PipelineError("config must be an exact PipelineConfig")
    _validate_authority(request, config)
    content, files, package_issues, untrusted_paths = _load_package(
        request.manifest, request.package_root,
    )
    candidates, image_evidence, candidate_issues, missing_image_paths = _load_candidates(
        request.manifest, content, untrusted_paths, package_issues,
    )
    indexes, _primary_types, _tags = _formal_indexes(request.baseline_database.path)
    state, indexes, _primary_types, _tags = _parent_context(
        request, config, indexes, _primary_types, _tags,
    )
    issues, adaptations, classifications = _classify(
        candidates, indexes, candidate_issues, _primary_types, _tags,
    )
    report_values = _report_values(
        request.manifest, candidates, issues, adaptations, classifications, files,
        missing_image_paths, state,
    )
    payload = _preflight_payload(
        request, candidates, issues, classifications, image_evidence, files,
        report_values, state,
    )
    report = V122ImportPreflightReport(
        preflight_sha256=_sha(_canonical(payload) + b"\n"), **report_values,
    )
    return V122ImportPreflightResult(request.manifest, state, candidates, issues, report)
