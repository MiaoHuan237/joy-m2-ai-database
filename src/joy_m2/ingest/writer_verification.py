"""Independent read-only verification for Task 9C candidate trees."""

from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path
import sqlite3

from joy_m2.config import PipelineConfig
from joy_m2.errors import InputFormatError, InputMissingError, PipelineError
from joy_m2.ingest.models import BatchImportManifest, ImportAdaptation, ImportCandidate, ImportFileEvidence, ImportIssue, ImportPreflightReport, ImportPreflightResult, as_plain_dict
from joy_m2.models import ArtifactRef, VerificationCheck, VerificationReport

from .writer_models import ImportApproval, V119VerificationRequest, V119WriterContract
from .writer_profiles import BASELINE_SHA256, BASELINE_SIZE_BYTES, CHECK_NAMES, FROZEN_SQLITE_HEADER_VERSION, TASK9_SCHEMA_SQL, canonical_json_bytes, canonical_json_file_bytes, is_sha256, normalized_sql, relative_path, sha256_bytes, sha256_file


def _file_projection(value) -> dict[str, object]:
    return {"relative_path": value.relative_path, "sha256": value.sha256, "size_bytes": value.size_bytes, "kind": value.kind}


def _manifest_source_projection(manifest) -> dict[str, object]:
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


def _report_projection(report) -> dict[str, object]:
    result = {field.name: getattr(report, field.name) for field in fields(report) if field.name != "preflight_sha256"}
    result["adaptations"] = [as_plain_dict(item) for item in report.adaptations]
    return result


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


def _frozen_baseline_bytes(
    reference: object,
    candidate_root: Path | None = None,
) -> bytes | None:
    if (
        not _reconstructs_exactly(reference, ArtifactRef)
        or reference.kind != "sqlite"
        or reference.sha256 != BASELINE_SHA256
        or reference.size_bytes != BASELINE_SIZE_BYTES
    ):
        return None
    try:
        path = reference.path.resolve(strict=True)
        if (
            not path.is_file()
            or path.is_symlink()
            or (
                candidate_root is not None
                and path.is_relative_to(candidate_root.resolve(strict=True))
            )
        ):
            return None
        data = path.read_bytes()
    except (OSError, RuntimeError, TypeError, ValueError):
        return None
    if len(data) != BASELINE_SIZE_BYTES or sha256_bytes(data) != BASELINE_SHA256:
        return None
    return data


def _sqlite_from_bytes(data: bytes) -> sqlite3.Connection:
    database = sqlite3.connect(":memory:")
    try:
        database.deserialize(data)
    except Exception:
        database.close()
        raise
    return database


def _sqlite_file_envelope_valid(data: bytes, baseline: bytes) -> bool:
    if len(data) < 100 or len(baseline) < 100:
        return False
    encoded_page_size = int.from_bytes(data[16:18], "big")
    page_size = 65_536 if encoded_page_size == 1 else encoded_page_size
    baseline_page_count = int.from_bytes(baseline[28:32], "big")
    page_count = int.from_bytes(data[28:32], "big")
    change_counter = int.from_bytes(data[24:28], "big")
    baseline_change_counter = int.from_bytes(baseline[24:28], "big")
    schema_cookie = int.from_bytes(data[40:44], "big")
    baseline_schema_cookie = int.from_bytes(baseline[40:44], "big")
    frozen_header_ranges = (
        (0, 24),
        (32, 40),
        (44, 60),
        (64, 92),
    )
    return (
        all(data[start:end] == baseline[start:end] for start, end in frozen_header_ranges)
        and 512 <= page_size <= 65_536
        and page_size & (page_size - 1) == 0
        and page_count >= baseline_page_count
        and len(data) == page_size * page_count
        and change_counter == baseline_change_counter + 2
        and schema_cookie == baseline_schema_cookie + 6
        and int.from_bytes(data[60:64], "big") == 119
        and int.from_bytes(data[92:96], "big") == change_counter
        and int.from_bytes(data[96:100], "big")
        == FROZEN_SQLITE_HEADER_VERSION
    )


def _frozen_baseline_identity(data: bytes) -> bool:
    database = None
    try:
        database = _sqlite_from_bytes(data)
        metadata = dict(database.execute("SELECT key,value FROM release_metadata_v2"))
        return (
            database.execute("PRAGMA user_version").fetchone() == (118,)
            and database.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            and database.execute("PRAGMA foreign_key_check").fetchall() == []
            and database.execute(
                "SELECT COUNT(*) FROM complete_questions_v2"
            ).fetchone()
            == (497,)
            and metadata.get("release_version") == "V1.18"
            and metadata.get("schema_version") == "complete-question-v1.0"
        )
    except (OSError, sqlite3.Error, TypeError, ValueError):
        return False
    finally:
        if database is not None:
            database.close()


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
        return (
            all(
                _reconstructs_exactly(item, ImportFileEvidence)
                for group in groups
                for item in group
            )
            and all(
                _reconstructs_exactly(item, ImportCandidate)
                for item in preflight.candidates
            )
            and all(
                _reconstructs_exactly(item, ImportIssue)
                for item in preflight.issues
            )
            and all(
                _reconstructs_exactly(item, ImportAdaptation)
                for item in report.adaptations
            )
            and _reconstructs_exactly(preflight, ImportPreflightResult)
        )
    except (AttributeError, PipelineError, RuntimeError, TypeError, ValueError):
        return False


def _authority_valid(request: V119VerificationRequest, candidate_root: Path) -> bool:
    try:
        preflight = request.preflight_result
        if (
            not _reconstructs_exactly(request, V119VerificationRequest)
            or not _nested_authority_valid(preflight, request.approval)
        ):
            return False
        baseline_bytes = _frozen_baseline_bytes(
            preflight.baseline_database,
            candidate_root,
        )
        if baseline_bytes is None or not _frozen_baseline_identity(baseline_bytes):
            return False
        report = preflight.report
        manifest = preflight.manifest
        candidates = preflight.candidates
        if type(candidates) is not tuple or any(type(item) is not ImportCandidate for item in candidates):
            return False
        ids = tuple(item.proposed_question_id for item in candidates)
        groups = (manifest.candidate_records, manifest.source_files, manifest.answer_files,
                  manifest.image_files, manifest.teacher_notes_files, manifest.common_errors_files)
        for group in groups:
            for item in group:
                relative_path(item.relative_path)
        evidence = tuple(sorted((item for group in groups for item in group), key=lambda item: item.relative_path))
        evidence_paths = tuple(item.relative_path for item in evidence)
        image_by_path = {item.relative_path: item for item in manifest.image_files}
        image_evidence = [
            {"proposed_question_id": candidate.proposed_question_id, "relative_path": path,
             "sha256": image_by_path[path].sha256, "size_bytes": image_by_path[path].size_bytes,
             "kind": image_by_path[path].kind, "role": role}
            for candidate in candidates
            for path, role in zip(candidate.image_paths, candidate.image_roles, strict=True)
        ]
        manifest_sha = sha256_bytes(canonical_json_file_bytes(_manifest_source_projection(manifest)))
        payload = {
            "schema": "task9-preflight-v1", "batch_id": manifest.batch_id,
            "target_release_version": manifest.target_release_version,
            "baseline": {"release_version": "V1.18", "schema_version": "complete-question-v1.0", "question_count": 497,
                         "sha256": preflight.baseline_database.sha256, "size_bytes": preflight.baseline_database.size_bytes,
                         "kind": preflight.baseline_database.kind},
            "manifest_policies": {name: getattr(manifest, name) for name in (
                "schema_version", "project", "module", "chapter", "language_policy", "split_policy",
                "difficulty_policy", "tag_policy", "answer_policy", "explanation_policy")},
            "candidate_record_order": [item.relative_path for item in manifest.candidate_records],
            "file_evidence": [as_plain_dict(item) for item in evidence],
            "candidates": [as_plain_dict(item) for item in candidates],
            "issues": [as_plain_dict(item) for item in preflight.issues],
            "duplicate_classifications": [
                {"candidate_id": item.proposed_question_id, "classification": "new_candidate", "reference_question_id": None, "evidence": None}
                for item in candidates
            ],
            "image_evidence": image_evidence,
            "report": _report_projection(report),
        }
        preflight_sha = sha256_bytes(canonical_json_file_bytes(payload))
        levels = tuple((level, sum(item.difficulty_level == level for item in candidates))
                       for level in range(1, 6) if any(item.difficulty_level == level for item in candidates))
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
            report.status == "READY FOR USER IMPORT APPROVAL" and report.batch_id == manifest.batch_id
            and report.manifest_sha256 == manifest_sha and report.preflight_sha256 == preflight_sha
            and report.baseline_version == "V1.18" and report.target_release_version == "V1.19"
            and report.before_count == 497 and report.detected_count == report.new_candidate_count == len(candidates)
            and report.duplicate_count == report.rejected_count == report.ambiguous_count == report.approved_count == 0
            and report.projected_after_count == 497 + len(candidates) and report.proposed_ids == ids and len(set(ids)) == len(ids)
            and report.readable_files == evidence_paths and report.unreadable_files == report.unsupported_files == ()
            and report.teacher_notes_file_count == len(manifest.teacher_notes_files)
            and report.common_errors_file_count == len(manifest.common_errors_files)
            and report.ambiguous_splits == ()
            and report.missing_images == report.orphan_images == report.warnings == report.blocking_errors == ()
            and report.missing_answers == missing_answers
            and report.missing_explanations == missing_explanations
            and report.incomplete_enrichments == incomplete_enrichments
            and report.level_counts == levels and preflight.issues == ()
            and request.approval.batch_id == manifest.batch_id
            and request.approval.preflight_sha256 == report.preflight_sha256
            and request.approval.target_release_version == "V1.19"
            and request.approval.statement == f"USER APPROVED IMPORT BATCH {manifest.batch_id} {report.preflight_sha256} V1.19"
        )
    except (AttributeError, KeyError, PipelineError, TypeError, ValueError):
        return False


def _baseline_object(request: V119VerificationRequest) -> dict[str, object]:
    baseline = request.preflight_result.baseline_database
    return {"release_version": "V1.18", "question_count": 497, "schema_version": "complete-question-v1.0",
            "sqlite": {"sha256": baseline.sha256, "size_bytes": baseline.size_bytes, "kind": "sqlite"}}


def _expected_image_projection(request: V119VerificationRequest):
    try:
        evidence = {
            item.relative_path: item
            for item in request.preflight_result.manifest.image_files
        }
        physical: dict[str, dict[str, object]] = {}
        database_rows = []
        digest_extensions: dict[str, str] = {}
        for candidate_order, candidate in enumerate(
            request.preflight_result.candidates
        ):
            for image_order, (source, digest, role) in enumerate(
                zip(
                    candidate.image_paths,
                    candidate.image_sha256s,
                    candidate.image_roles,
                    strict=True,
                )
            ):
                source = relative_path(source)
                suffix = Path(source).suffix.lower()
                declared = evidence.get(source)
                if (
                    suffix not in {".jpg", ".jpeg", ".png"}
                    or not is_sha256(digest)
                    or declared is None
                    or type(declared) is not ImportFileEvidence
                    or declared.kind != "image"
                    or declared.sha256 != digest
                    or type(declared.size_bytes) is not int
                    or declared.size_bytes < 0
                ):
                    return None, None
                extension = ".jpg" if suffix in {".jpg", ".jpeg"} else ".png"
                if digest_extensions.setdefault(digest, extension) != extension:
                    return None, None
                destination = (
                    f"{request.contract.image_root}/{digest[:2]}/"
                    f"{digest}{extension}"
                )
                size = declared.size_bytes
                current = physical.setdefault(
                    destination,
                    {
                        "relative_path": destination,
                        "sha256": digest,
                        "size_bytes": size,
                        "kind": "image",
                        "bindings": [],
                    },
                )
                if current["sha256"] != digest or current["size_bytes"] != size:
                    return None, None
                current["bindings"].append(
                    {
                        "proposed_question_id": candidate.proposed_question_id,
                        "image_order": image_order,
                        "source_relative_path": source,
                        "role": role,
                    }
                )
                database_rows.append(
                    (
                        request.approval.batch_id,
                        candidate.proposed_question_id,
                        image_order,
                        source,
                        destination,
                        digest,
                        size,
                        "image",
                        role,
                    )
                )
        return [physical[name] for name in sorted(physical)], tuple(database_rows)
    except (AttributeError, PipelineError, TypeError, ValueError):
        return None, None


def _artifact_identity(root: Path, relative: str, kind: str):
    try:
        path = root / relative_path(relative)
        if not path.is_file() or path.is_symlink():
            return None
        return {"relative_path": relative, "sha256": sha256_file(path), "size_bytes": path.stat().st_size, "kind": kind}
    except (OSError, InputFormatError):
        return None


def _expected_manifest(request: V119VerificationRequest, root: Path):
    images, _ = _expected_image_projection(request)
    database = _artifact_identity(root, request.contract.database_filename, "sqlite")
    rollback = _artifact_identity(root, request.contract.rollback_filename, "rollback")
    if images is None or database is None or rollback is None:
        return None
    report = request.preflight_result.report
    manifest = request.preflight_result.manifest
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
        "database": database, "images": images,
        "candidate_record_evidence": [_file_projection(item) for item in manifest.candidate_records],
        "source_evidence": [_file_projection(item) for item in manifest.source_files],
        "answer_evidence": [_file_projection(item) for item in manifest.answer_files],
        "teacher_notes_evidence": [_file_projection(item) for item in manifest.teacher_notes_files],
        "common_errors_evidence": [_file_projection(item) for item in manifest.common_errors_files],
        "rollback": rollback,
    }


def _read_manifest(path: Path):
    if not path.exists() and not path.is_symlink():
        raise InputMissingError("candidate manifest is missing")
    if path.is_symlink() or not path.is_file():
        raise InputFormatError("candidate manifest is unreadable")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise InputFormatError("candidate manifest is unreadable") from error
    try:
        return raw, json.loads(raw.decode("utf-8"))
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as error:
        raise InputFormatError("candidate manifest cannot establish verification context") from error


def _read_sums(path: Path):
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file():
        raise InputFormatError("SHA256SUMS is unreadable")
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise InputFormatError("SHA256SUMS is unreadable") from error
    if not text or not text.endswith("\n"):
        raise InputFormatError("SHA256SUMS syntax is malformed")
    entries = []
    for line in text.splitlines(keepends=True):
        if not line.endswith("\n") or len(line) < 67 or line[64:66] != "  " or not is_sha256(line[:64]):
            raise InputFormatError("SHA256SUMS syntax is malformed")
        relative = line[66:-1]
        if relative != relative.strip():
            raise InputFormatError("SHA256SUMS syntax is malformed")
        try:
            relative_path(relative)
        except InputFormatError as error:
            raise InputFormatError("SHA256SUMS path is malformed") from error
        entries.append((line[:64], relative))
    return tuple(entries)


def _filesystem_state(root: Path):
    files = set()
    directories = set()
    valid = True
    try:
        for item in root.rglob("*"):
            relative = item.relative_to(root).as_posix()
            if item.is_symlink():
                valid = False
            elif item.is_dir():
                directories.add(relative)
            elif item.is_file():
                files.add(relative)
            else:
                valid = False
    except OSError:
        valid = False
    return files, directories, valid


def _tree_fingerprint(root: Path):
    values = []
    try:
        for item in sorted(root.rglob("*")):
            relative = item.relative_to(root).as_posix()
            if item.is_symlink():
                values.append((relative, "symlink", None))
            elif item.is_dir():
                values.append((relative, "directory", None))
            elif item.is_file():
                values.append((relative, "file", sha256_file(item)))
            else:
                values.append((relative, "other", None))
    except OSError:
        return None
    return tuple(values)


def _exact_json_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return (
            set(actual) == set(expected)
            and all(_exact_json_equal(actual[key], expected[key]) for key in expected)
        )
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            _exact_json_equal(left, right)
            for left, right in zip(actual, expected, strict=True)
        )
    return actual == expected


def _contract_valid(contract: object) -> bool:
    if type(contract) is not V119WriterContract:
        return False
    expected = {
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
        ),
        "required_candidate_tables": (
            "task9_import_batches_v1",
            "task9_import_candidates_v1",
            "task9_import_images_v1",
            "task9_import_taxonomy_v1",
        ),
        "required_candidate_views": ("task9_candidate_questions_v1",),
    }
    return all(
        type(getattr(contract, name, None)) is type(value)
        and getattr(contract, name) == value
        for name, value in expected.items()
    )


def _candidate_rows(request: V119VerificationRequest) -> tuple[tuple[object, ...], ...]:
    destination_paths: dict[str, list[str]] = {}
    _, image_rows = _expected_image_projection(request)
    if image_rows is None:
        return ()
    for row in image_rows:
        destination_paths.setdefault(row[1], []).append(row[4])
    result = []
    for candidate_order, candidate in enumerate(request.preflight_result.candidates):
        values = [getattr(candidate, field.name) for field in fields(candidate)]
        for index in (16, 17, 18, 20):
            values[index] = canonical_json_bytes(values[index]).decode("utf-8")
        result.append(
            (
                request.approval.batch_id,
                candidate_order,
                *values,
                canonical_json_bytes(
                    destination_paths.get(candidate.proposed_question_id, [])
                ).decode("utf-8"),
                "candidate",
                0,
            )
        )
    return tuple(result)


def _batch_rows(request: V119VerificationRequest) -> tuple[tuple[object, ...], ...]:
    preflight = request.preflight_result
    report = preflight.report
    return (
        (
            request.approval.batch_id,
            "V1.19",
            request.contract.candidate_database_schema,
            report.preflight_sha256,
            report.manifest_sha256,
            request.approval.statement,
            "V1.18",
            preflight.baseline_database.sha256,
            497,
            len(preflight.candidates),
            report.projected_after_count,
            "candidate",
        ),
    )


def _taxonomy_rows(request: V119VerificationRequest) -> tuple[tuple[object, ...], ...]:
    batch_id = request.approval.batch_id
    primary_types = tuple(
        sorted({candidate.primary_type for candidate in request.preflight_result.candidates})
    )
    tags = tuple(
        sorted(
            {
                tag
                for candidate in request.preflight_result.candidates
                for tag in candidate.tags
            }
        )
    )
    return tuple(
        (batch_id, kind, value, order)
        for kind, values in (("primary_type", primary_types), ("tag", tags))
        for order, value in enumerate(values, start=1)
    )


def _master_rows(database: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        database.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        )
    )


def _logical_rows(database: sqlite3.Connection, name: str) -> tuple[tuple[object, ...], ...]:
    rows = tuple(database.execute(f'SELECT * FROM "{name}"'))
    return tuple(sorted(rows, key=repr))


def _inspect_sqlite(
    request: V119VerificationRequest, database_path: Path
) -> dict[str, bool]:
    state = {
        "readability": False,
        "integrity": False,
        "foreign_keys": False,
        "schema": False,
        "projection": False,
        "baseline": False,
        "count": False,
        "publication": False,
        "images": False,
    }
    if not database_path.is_file() or database_path.is_symlink():
        return state
    candidate = None
    baseline = None
    try:
        baseline_bytes = _frozen_baseline_bytes(
            request.preflight_result.baseline_database,
            database_path.parent,
        )
        if baseline_bytes is None:
            return state
        candidate_bytes = database_path.read_bytes()
        if not _sqlite_file_envelope_valid(candidate_bytes, baseline_bytes):
            return state
        candidate = _sqlite_from_bytes(candidate_bytes)
        baseline = _sqlite_from_bytes(baseline_bytes)
        baseline_identity = _frozen_baseline_identity(baseline_bytes)
        if baseline_identity:
            candidate.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
            state["readability"] = True
            state["integrity"] = candidate.execute(
                "PRAGMA integrity_check"
            ).fetchall() == [("ok",)]
            state["foreign_keys"] = candidate.execute(
                "PRAGMA foreign_key_check"
            ).fetchall() == []

            baseline_master = _master_rows(baseline)
            candidate_master = _master_rows(candidate)
            baseline_by_name = {row[1]: row for row in baseline_master}
            candidate_by_name = {row[1]: row for row in candidate_master}
            task9_objects = {
                row[1]: row
                for row in candidate_master
                if str(row[1]).startswith("task9_")
            }
            expected_task9 = {}
            for statement in TASK9_SCHEMA_SQL:
                words = statement.split()
                kind = words[1].lower()
                name = words[2]
                expected_task9[name] = (kind, name, name if kind == "table" else name, statement)
            schema_sql_valid = (
                set(task9_objects) == set(expected_task9)
                and all(
                    task9_objects[name][0] == expected_task9[name][0]
                    and normalized_sql(task9_objects[name][3])
                    == normalized_sql(expected_task9[name][3])
                    for name in expected_task9
                )
            )
            preserved_schema = all(
                candidate_by_name.get(name) == row
                for name, row in baseline_by_name.items()
            )
            no_extra_objects = set(candidate_by_name) == (
                set(baseline_by_name) | set(expected_task9)
            )
            state["schema"] = (
                candidate.execute("PRAGMA user_version").fetchone() == (119,)
                and schema_sql_valid
                and preserved_schema
                and no_extra_objects
            )

            data_names = tuple(
                row[1] for row in baseline_master if row[0] in {"table", "view"}
            )
            state["baseline"] = baseline_identity and preserved_schema and all(
                _logical_rows(candidate, name) == _logical_rows(baseline, name)
                for name in data_names
            )

            _, image_rows = _expected_image_projection(request)
            actual_batch = tuple(candidate.execute("SELECT * FROM task9_import_batches_v1"))
            actual_candidates = tuple(
                candidate.execute(
                    "SELECT * FROM task9_import_candidates_v1 "
                    "ORDER BY candidate_order"
                )
            )
            actual_images = tuple(
                candidate.execute(
                    "SELECT * FROM task9_import_images_v1 "
                    "ORDER BY proposed_question_id,image_order"
                )
            )
            actual_taxonomy = tuple(
                candidate.execute(
                    "SELECT * FROM task9_import_taxonomy_v1 "
                    "ORDER BY taxonomy_kind,sort_order"
                )
            )
            expected_images = tuple(
                sorted(image_rows or (), key=lambda row: (row[1], row[2]))
            )
            state["images"] = image_rows is not None and actual_images == expected_images
            state["projection"] = (
                actual_batch == _batch_rows(request)
                and actual_candidates == _candidate_rows(request)
                and actual_taxonomy == _taxonomy_rows(request)
                and tuple(
                    candidate.execute(
                        "SELECT * FROM task9_candidate_questions_v1 "
                        "ORDER BY candidate_order"
                    )
                )
                == _candidate_rows(request)
            )
            candidate_count = candidate.execute(
                "SELECT COUNT(*) FROM task9_import_candidates_v1"
            ).fetchone()
            baseline_count = candidate.execute(
                "SELECT COUNT(*) FROM complete_questions_v2"
            ).fetchone()
            state["count"] = (
                baseline_count == (497,)
                and candidate_count == (len(request.preflight_result.candidates),)
                and request.preflight_result.report.projected_after_count
                == 497 + len(request.preflight_result.candidates)
            )
            proposed_ids = tuple(
                candidate.proposed_question_id
                for candidate in request.preflight_result.candidates
            )
            placeholders = ",".join("?" for _ in proposed_ids)
            leaked_v2 = 0
            leaked_selectable = 0
            if proposed_ids:
                leaked_v2 = candidate.execute(
                    f"SELECT COUNT(*) FROM complete_questions_v2 WHERE question_id IN ({placeholders})",
                    proposed_ids,
                ).fetchone()[0]
                leaked_selectable = candidate.execute(
                    f"SELECT COUNT(*) FROM selectable_complete_questions_v2 WHERE question_id IN ({placeholders})",
                    proposed_ids,
                ).fetchone()[0]
            state["publication"] = (
                candidate.execute(
                    "SELECT COUNT(*) FROM task9_import_candidates_v1 "
                    "WHERE record_status!='candidate' OR selectable!=0"
                ).fetchone()
                == (0,)
                and candidate.execute(
                    "SELECT COUNT(*) FROM task9_import_batches_v1 "
                    "WHERE record_status!='candidate'"
                ).fetchone()
                == (0,)
                and leaked_v2 == 0
                and leaked_selectable == 0
            )
    except (OSError, sqlite3.Error, TypeError, ValueError):
        return state
    finally:
        if candidate is not None:
            candidate.close()
        if baseline is not None:
            baseline.close()
    return state


def _rollback_valid(
    request: V119VerificationRequest, root: Path, expected_files: set[str]
) -> bool:
    path = root / request.contract.rollback_filename
    try:
        if path.is_symlink() or not path.is_file():
            return False
        raw = path.read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
        expected = {
            "schema_version": "task9-v119-rollback-v1",
            "action": "delete_unpromoted_candidate_tree",
            "batch_id": request.approval.batch_id,
            "preflight_sha256": request.approval.preflight_sha256,
            "baseline": _baseline_object(request),
            "candidate_artifacts": sorted(expected_files),
        }
        return (
            _exact_json_equal(parsed, expected)
            and raw == canonical_json_file_bytes(parsed)
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        return False


def _report(checks: dict[str, bool]) -> VerificationReport:
    values = tuple(
        VerificationCheck(name, bool(checks.get(name, False)), "PASS" if checks.get(name, False) else "FAIL")
        for name in CHECK_NAMES
    )
    return VerificationReport(
        "PASS" if all(check.passed for check in values) else "FAIL", values
    )


def verify_v119_candidate(
    request: V119VerificationRequest, config: PipelineConfig
) -> VerificationReport:
    """Verify one temporary or staged V1.19 candidate tree without mutation."""
    if type(request) is not V119VerificationRequest:
        raise PipelineError("request must be an exact V119VerificationRequest")
    if type(config) is not PipelineConfig:
        raise PipelineError("config must be an exact PipelineConfig")
    if (
        not _reconstructs_exactly(request, V119VerificationRequest)
        or not _reconstructs_exactly(config, PipelineConfig)
    ):
        raise PipelineError("verification request carrier is invalid")
    if (
        not _contract_valid(request.contract)
        or not _reconstructs_exactly(request.contract, V119WriterContract)
        or not _nested_authority_valid(
            request.preflight_result,
            request.approval,
        )
    ):
        raise PipelineError("verification request carrier is invalid")
    try:
        root = config.require_staging_output(request.candidate_dir)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise PipelineError("candidate directory locator is invalid") from error
    if root == config.staging_root:
        raise PipelineError("candidate directory must be a strict staging descendant")
    if not root.exists():
        raise InputMissingError("candidate directory does not exist")
    if not root.is_dir() or root.is_symlink():
        raise InputFormatError("candidate root must be a contained directory")

    initial_fingerprint = _tree_fingerprint(root)

    manifest_raw, parsed_manifest = _read_manifest(
        root / request.contract.manifest_filename
    )
    sums = _read_sums(root / request.contract.sha256s_filename)
    authority_valid = _authority_valid(request, root)
    image_entries, _ = (
        _expected_image_projection(request)
        if authority_valid
        else (None, None)
    )
    image_paths = {
        item["relative_path"] for item in image_entries or ()
    }
    expected_files = {
        request.contract.database_filename,
        request.contract.manifest_filename,
        request.contract.sha256s_filename,
        request.contract.rollback_filename,
        *image_paths,
    }
    files, directories, filesystem_types_valid = _filesystem_state(root)
    expected_directories = {
        parent.as_posix()
        for relative in expected_files
        for parent in Path(relative).parents
        if parent.as_posix() != "."
    }
    filesystem_valid = (
        filesystem_types_valid
        and files == expected_files
        and directories == expected_directories
    )

    expected_manifest = _expected_manifest(request, root) if authority_valid else None
    try:
        manifest_valid = (
            expected_manifest is not None
            and _exact_json_equal(parsed_manifest, expected_manifest)
            and manifest_raw == canonical_json_file_bytes(parsed_manifest)
        )
    except (TypeError, ValueError):
        manifest_valid = False

    expected_sum_paths = tuple(
        sorted(expected_files - {request.contract.sha256s_filename})
    )
    sums_valid = False
    if sums is not None:
        try:
            sums_valid = (
                tuple(path for _, path in sums) == expected_sum_paths
                and len({path for _, path in sums}) == len(sums)
                and filesystem_types_valid
                and files - {request.contract.sha256s_filename}
                == set(expected_sum_paths)
                and all(
                    (root / relative).is_file()
                    and not (root / relative).is_symlink()
                    and sha256_file(root / relative) == digest
                    for digest, relative in sums
                )
            )
        except OSError:
            sums_valid = False

    artifact_references = False
    try:
        if type(parsed_manifest) is dict and expected_manifest is not None:
            expected_artifacts = (
                expected_manifest["database"],
                expected_manifest["rollback"],
                *expected_manifest["images"],
            )
            actual_artifacts = (
                parsed_manifest.get("database"),
                parsed_manifest.get("rollback"),
                *(parsed_manifest.get("images") if type(parsed_manifest.get("images")) is list else ()),
            )
            artifact_references = _exact_json_equal(
                list(actual_artifacts), list(expected_artifacts)
            )
    except (KeyError, TypeError, ValueError):
        artifact_references = False

    image_projection = False
    if image_entries is not None and filesystem_valid:
        try:
            image_projection = all(
                (root / item["relative_path"]).is_file()
                and not (root / item["relative_path"]).is_symlink()
                and sha256_file(root / item["relative_path"]) == item["sha256"]
                and (root / item["relative_path"]).stat().st_size == item["size_bytes"]
                for item in image_entries
            )
        except OSError:
            image_projection = False

    sqlite_state = (
        _inspect_sqlite(request, root / request.contract.database_filename)
        if authority_valid
        else {
            "readability": False,
            "integrity": False,
            "foreign_keys": False,
            "schema": False,
            "projection": False,
            "baseline": False,
            "count": False,
            "publication": False,
            "images": False,
        }
    )
    image_projection = image_projection and sqlite_state["images"]
    rollback_valid = (
        _rollback_valid(request, root, expected_files) if authority_valid else False
    )
    rollback_valid = rollback_valid and filesystem_types_valid and files == expected_files
    final_files, final_directories, final_types_valid = _filesystem_state(root)
    final_fingerprint = _tree_fingerprint(root)
    filesystem_valid = (
        filesystem_valid
        and final_types_valid
        and final_files == expected_files
        and final_directories == expected_directories
        and initial_fingerprint is not None
        and final_fingerprint == initial_fingerprint
    )
    checks = {
        "candidate_directory": True,
        "manifest_contract": manifest_valid,
        "preflight_approval_binding": authority_valid,
        "filesystem_closure": filesystem_valid,
        "sha256sums_closure": sums_valid,
        "artifact_references": artifact_references,
        "rollback_contract": rollback_valid,
        "image_projection": image_projection,
        "sqlite_readability": sqlite_state["readability"],
        "sqlite_integrity": sqlite_state["integrity"],
        "sqlite_foreign_keys": sqlite_state["foreign_keys"],
        "sqlite_schema": sqlite_state["schema"],
        "sqlite_projection": sqlite_state["projection"],
        "baseline_preservation": sqlite_state["baseline"],
        "count_closure": sqlite_state["count"],
        "publication_boundary": sqlite_state["publication"],
    }
    return _report(checks)
