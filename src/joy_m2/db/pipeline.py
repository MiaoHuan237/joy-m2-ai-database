"""Transactional V1.17 and V1.18 SQLite database construction."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile

from ..errors import (
    BaselineMismatchError,
    DatabaseIntegrityError,
    ForeignKeyViolationError,
    InputMissingError,
    OutputConflictError,
    PipelineError,
)
from ..models import (
    ArtifactRef,
    AuditedBatch,
    DatabaseArtifact,
    DatabaseBuildRequest,
    DatabaseContract,
    VerificationCheck,
    VerificationReport,
    V117ReleaseBatch,
)
from .profiles import (
    DB_TABLE_COLUMNS,
    FROZEN_SQLITE_HEADER_VERSION,
    V117_PRIMARY_TYPES,
    V117_SCHEMA_SQL,
    V117_TAGS,
    canonical_json,
    v117_database_row,
    v118_database_row,
    v118_external_record,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_sqlite_header(path: Path) -> None:
    with path.open("r+b") as database_file:
        database_file.seek(96)
        database_file.write(FROZEN_SQLITE_HEADER_VERSION.to_bytes(4, "big"))


def _require_artifact(reference: ArtifactRef, *, kind: str) -> Path:
    if type(reference) is not ArtifactRef:
        raise PipelineError("database inputs must be ArtifactRef values")
    path = reference.path
    if not path.is_file():
        raise InputMissingError(f"required {kind} input does not exist: {path}")
    if reference.kind != kind:
        raise BaselineMismatchError(f"expected {kind} input kind")
    if path.stat().st_size != reference.size_bytes or _sha256(path) != reference.sha256:
        raise BaselineMismatchError(f"{kind} input identity does not match ArtifactRef")
    return path


def _load_manifest(reference: ArtifactRef) -> dict:
    path = _require_artifact(reference, kind="json")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise BaselineMismatchError("baseline manifest cannot be decoded") from error
    if type(value) is not dict:
        raise BaselineMismatchError("baseline manifest must contain an object")
    return value


def _database_objects(database: sqlite3.Connection) -> tuple[set[str], set[str]]:
    rows = database.execute(
        "SELECT type,name FROM sqlite_master WHERE type IN ('table','view')"
    ).fetchall()
    return (
        {name for object_type, name in rows if object_type == "table"},
        {name for object_type, name in rows if object_type == "view"},
    )


def _validate_baseline(request: DatabaseBuildRequest) -> tuple[Path, dict]:
    baseline = _require_artifact(request.baseline_database, kind="sqlite")
    manifest = _load_manifest(request.baseline_manifest)
    digest = request.baseline_database.sha256
    if request.release_spec.baseline_sqlite_sha256 != digest:
        raise BaselineMismatchError("release spec does not bind the baseline database")
    expected_manifest_identity = {
        "release_version": "V1.17",
        "release_status": "formal",
        "schema_version": "complete-question-v1.0",
        "release_model": "transitional-dual-layer",
    }
    if any(
        manifest.get(field_name) != expected
        for field_name, expected in expected_manifest_identity.items()
    ):
        raise BaselineMismatchError(
            "baseline manifest identity does not match the frozen V1.17 manifest"
        )

    profile = request.contract.profile
    if profile == "V1.18":
        artifacts = manifest.get("artifact_sha256")
        if type(artifacts) is not dict:
            raise BaselineMismatchError("manifest lacks the V1.17 artifact digest map")
        bound = artifacts.get(baseline.name)
        if bound != digest:
            raise BaselineMismatchError("manifest does not bind the V1.17 baseline database")
    elif profile == "V1.17":
        if manifest.get("baseline_v116_sqlite_sha256") != digest:
            raise BaselineMismatchError("manifest does not bind the V1.16 baseline database")
    else:
        raise PipelineError("database profile must be V1.17 or V1.18")

    try:
        with sqlite3.connect(f"file:{baseline}?mode=ro", uri=True) as database:
            integrity = database.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_keys = database.execute("PRAGMA foreign_key_check").fetchall()
            tables, views = _database_objects(database)
            if integrity != "ok":
                raise DatabaseIntegrityError("baseline SQLite integrity check failed")
            if foreign_keys:
                raise ForeignKeyViolationError("baseline SQLite foreign key check failed")
            if profile == "V1.18":
                valid = (
                    database.execute("PRAGMA user_version").fetchone()[0] == 117
                    and "complete_questions_v2" in tables
                    and "complete_questions" in views
                    and database.execute(
                        "SELECT COUNT(*) FROM complete_questions_v2"
                    ).fetchone()[0]
                    == 45
                    and database.execute(
                        "SELECT COUNT(*) FROM complete_questions"
                    ).fetchone()[0]
                    == 497
                )
            else:
                valid = (
                    database.execute("PRAGMA user_version").fetchone()[0] == 0
                    and {"questions", "sources", "topics", "question_topics"} <= tables
                    and "complete_questions" in views
                    and database.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
                    == 1517
                    and database.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
                    == 24
                    and database.execute(
                        "SELECT COUNT(*) FROM complete_questions"
                    ).fetchone()[0]
                    == 497
                )
            if not valid:
                raise DatabaseIntegrityError(
                    f"{profile} baseline database structure does not match"
                )
    except (DatabaseIntegrityError, ForeignKeyViolationError):
        raise
    except sqlite3.Error as error:
        raise DatabaseIntegrityError("baseline SQLite cannot be inspected") from error
    return baseline, manifest


def _validate_request(request: DatabaseBuildRequest) -> None:
    if type(request) is not DatabaseBuildRequest:
        raise PipelineError("request must be a DatabaseBuildRequest")
    profile = request.contract.profile
    expected = {
        "V1.17": (V117ReleaseBatch, "V1.17", "V1.16", 117),
        "V1.18": (AuditedBatch, "V1.18", "V1.17", 118),
    }.get(profile)
    if expected is None:
        raise PipelineError("database profile must be V1.17 or V1.18")
    batch_type, release_version, baseline_version, user_version = expected
    if type(request.batch) is not batch_type:
        raise PipelineError(f"{profile} database profile received the wrong batch type")
    if (
        request.release_spec.release_version != release_version
        or request.release_spec.baseline_version != baseline_version
        or request.release_spec.schema_version != "complete-question-v1.0"
        or request.contract.expected_user_version != user_version
    ):
        raise PipelineError("database release spec and contract profile do not match")
    if len(request.batch.records) != request.contract.expected_new_question_count:
        raise PipelineError("database batch count does not match the contract")
    if profile == "V1.18" and any(
        record.task4_compatibility is not None
        or record.release_compatibility is None
        or record.release_compatibility.formal_release_version != "V1.18"
        or record.question.publication_evidence.record_status != "audit_passed"
        for record in request.batch.records
    ):
        raise PipelineError(
            "V1.18 database profile requires audit-passed V1.18 records"
        )


def _insert_row(database: sqlite3.Connection, row: dict[str, object]) -> None:
    placeholders = ",".join("?" for _ in DB_TABLE_COLUMNS)
    database.execute(
        f"INSERT INTO complete_questions_v2 ({','.join(DB_TABLE_COLUMNS)}) "
        f"VALUES ({placeholders})",
        [row[column] for column in DB_TABLE_COLUMNS],
    )


def _build_v118(
    database: sqlite3.Connection,
    batch: AuditedBatch,
    baseline_sha256: str,
) -> None:
    database.execute("BEGIN IMMEDIATE")
    for record in batch.records:
        _insert_row(database, v118_database_row(record))
        database.executemany(
            "INSERT INTO complete_question_tags_v2(question_id,tag,tag_order) VALUES (?,?,?)",
            [
                (record.question.question_id, tag, index)
                for index, tag in enumerate(record.question.tags, start=1)
            ],
        )
    database.execute("DELETE FROM complete_question_taxonomy_v2")
    primary_types = [
        row[0]
        for row in database.execute(
            "SELECT DISTINCT primary_type FROM complete_questions_v2 ORDER BY primary_type"
        )
    ]
    tags = [
        row[0]
        for row in database.execute(
            "SELECT DISTINCT tag FROM complete_question_tags_v2 ORDER BY tag"
        )
    ]
    database.executemany(
        "INSERT INTO complete_question_taxonomy_v2(taxonomy_kind,value,sort_order) "
        "VALUES ('primary_type',?,?)",
        [(value, index) for index, value in enumerate(primary_types, start=1)],
    )
    database.executemany(
        "INSERT INTO complete_question_taxonomy_v2(taxonomy_kind,value,sort_order) "
        "VALUES ('tag',?,?)",
        [(value, index) for index, value in enumerate(tags, start=1)],
    )
    metadata = {
        "release_version": "V1.18",
        "release_model": "full-v2-with-legacy-compatibility",
        "schema_version": "complete-question-v1.0",
        "approved_at": "2026-08-08T21:00:00+08:00",
        "approved_by": "Joy",
        "baseline_version": "V1.17",
        "baseline_sqlite_sha256": baseline_sha256,
        "legacy_question_rows": "1517",
        "legacy_complete_questions": "497",
        "audited_v2_questions": "497",
        "task6_imported_questions": "452",
        "remaining_unmigrated_complete_questions": "0",
    }
    database.executemany(
        "INSERT OR REPLACE INTO release_metadata_v2(key,value) VALUES (?,?)",
        sorted(metadata.items()),
    )
    audit_hash = _sha256_text(
        canonical_json([v118_external_record(record) for record in batch.records])
    )
    database.execute(
        "INSERT INTO import_runs_v2 VALUES (?,?,?,?,?,?,?,?)",
        (
            "TASK6-2026-08-08-FULL-452",
            "V1.18",
            "2026-08-08T21:00:00+08:00",
            "Joy",
            baseline_sha256,
            audit_hash,
            452,
            "completed",
        ),
    )
    database.execute("PRAGMA user_version=118")
    database.commit()


def _build_v117(
    database: sqlite3.Connection,
    batch: V117ReleaseBatch,
    baseline_sha256: str,
    manifest: dict,
) -> None:
    database.executescript(V117_SCHEMA_SQL)
    metadata = {
        "release_version": "V1.17",
        "release_model": "transitional-dual-layer",
        "schema_version": "complete-question-v1.0",
        "approved_at": "2026-08-08T20:00:00+08:00",
        "approved_by": "Joy",
        "baseline_version": "V1.16",
        "baseline_sqlite_sha256": baseline_sha256,
        "legacy_question_rows": "1517",
        "legacy_complete_questions": "497",
        "audited_v2_questions": "45",
        "remaining_unmigrated_complete_questions": "452",
    }
    database.executemany(
        "INSERT INTO release_metadata_v2(key,value) VALUES (?,?)",
        sorted(metadata.items()),
    )
    for record in batch.records:
        _insert_row(database, v117_database_row(record))
        question = record.audited_record.question
        database.executemany(
            "INSERT INTO complete_question_tags_v2(question_id,tag,tag_order) VALUES (?,?,?)",
            [
                (question.question_id, tag, index)
                for index, tag in enumerate(question.tags, start=1)
            ],
        )
        database.executemany(
            "INSERT INTO complete_question_corrections_v2 "
            "(question_id,correction_order,field_name,error_origin,original_text,"
            "corrected_text,reason,evidence) VALUES (?,?,?,?,?,?,?,?)",
            [
                (
                    question.question_id,
                    index,
                    correction.field,
                    correction.error_origin,
                    correction.original,
                    correction.corrected,
                    correction.reason,
                    correction.evidence,
                )
                for index, correction in enumerate(question.corrections, start=1)
            ],
        )
    for kind, values in (("primary_type", V117_PRIMARY_TYPES), ("tag", V117_TAGS)):
        database.executemany(
            "INSERT INTO complete_question_taxonomy_v2(taxonomy_kind,value,sort_order) "
            "VALUES (?,?,?)",
            [(kind, value, index) for index, value in enumerate(values, start=1)],
        )
    candidate_sha256 = manifest.get("task4_candidate_sha256")
    if type(candidate_sha256) is not str:
        raise BaselineMismatchError("manifest lacks the V1.17 candidate digest projection")
    database.execute(
        "INSERT INTO import_runs_v2 VALUES (?,?,?,?,?,?,?,?)",
        (
            "TASK5-2026-08-08-M2QD-DA-45",
            "V1.17",
            "2026-08-08T20:00:00+08:00",
            "Joy",
            baseline_sha256,
            candidate_sha256,
            45,
            "completed",
        ),
    )
    database.execute("PRAGMA user_version=117")
    database.commit()


def _check(name: str, actual: object, expected: object) -> VerificationCheck:
    return VerificationCheck(
        name=name,
        passed=actual == expected,
        detail=f"actual={actual!r}; expected={expected!r}",
    )


def verify_database(path: Path, contract: DatabaseContract) -> VerificationReport:
    """Verify a built database without mutating it."""

    path = path.resolve()
    if not path.is_file():
        raise InputMissingError(f"database does not exist: {path}")
    checks: list[VerificationCheck] = []
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
            tables, views = _database_objects(database)
            existing_count = (
                database.execute(
                    "SELECT COUNT(*) FROM complete_questions_v2 WHERE source_order <= 45"
                ).fetchone()[0]
                if contract.profile == "V1.18"
                else 0
            )
            new_count = (
                database.execute(
                    "SELECT COUNT(*) FROM complete_questions_v2 WHERE source_order > 45"
                ).fetchone()[0]
                if contract.profile == "V1.18"
                else database.execute(
                    "SELECT COUNT(*) FROM complete_questions_v2"
                ).fetchone()[0]
            )
            checks.extend(
                (
                    _check("user_version", database.execute("PRAGMA user_version").fetchone()[0], contract.expected_user_version),
                    _check("integrity_check", database.execute("PRAGMA integrity_check").fetchone()[0], "ok"),
                    _check("foreign_key_check", database.execute("PRAGMA foreign_key_check").fetchall(), []),
                    _check("required_tables", tuple(sorted(set(contract.required_tables) - tables)), ()),
                    _check("required_views", tuple(sorted(set(contract.required_views) - views)), ()),
                    _check("question_count", database.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone()[0], contract.expected_question_count),
                    _check("existing_question_count", existing_count, contract.expected_existing_question_count),
                    _check("new_question_count", new_count, contract.expected_new_question_count),
                    _check(
                        "answer_status_counts",
                        tuple(sorted(database.execute("SELECT answer_status,COUNT(*) FROM complete_questions_v2 GROUP BY answer_status").fetchall())),
                        tuple(contract.expected_answer_status_counts),
                    ),
                    _check("journal_mode", database.execute("PRAGMA journal_mode").fetchone()[0], contract.journal_mode),
                )
            )
    except sqlite3.Error as error:
        raise DatabaseIntegrityError("database verification could not be completed") from error
    return VerificationReport(
        status="PASS" if all(check.passed for check in checks) else "FAIL",
        checks=tuple(checks),
    )


def build_database(request: DatabaseBuildRequest) -> DatabaseArtifact:
    """Build and atomically publish one profile-specific SQLite database."""

    _validate_request(request)
    if request.output_path.exists():
        raise OutputConflictError(f"database output already exists: {request.output_path}")
    baseline, manifest = _validate_baseline(request)

    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{request.output_path.name}.",
        suffix=".tmp",
        dir=request.output_path.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copyfile(baseline, temporary)
        try:
            with sqlite3.connect(temporary) as database:
                database.execute("PRAGMA foreign_keys=ON")
                database.execute("PRAGMA journal_mode=DELETE")
                if request.contract.profile == "V1.18":
                    _build_v118(database, request.batch, request.baseline_database.sha256)
                else:
                    _build_v117(
                        database,
                        request.batch,
                        request.baseline_database.sha256,
                        manifest,
                    )
                foreign_keys = database.execute("PRAGMA foreign_key_check").fetchall()
                if foreign_keys:
                    raise ForeignKeyViolationError("candidate SQLite foreign key check failed")
                if database.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise DatabaseIntegrityError("candidate SQLite integrity check failed")
                database.execute("VACUUM")
        except sqlite3.IntegrityError as error:
            if "FOREIGN KEY" in str(error).upper():
                raise ForeignKeyViolationError(
                    "candidate row violates a baseline foreign key"
                ) from error
            raise DatabaseIntegrityError("candidate row violates SQLite integrity") from error
        except sqlite3.Error as error:
            raise DatabaseIntegrityError("candidate SQLite build failed") from error

        _normalize_sqlite_header(temporary)
        report = verify_database(temporary, request.contract)
        if report.status != "PASS":
            raise DatabaseIntegrityError("candidate database verification failed")
        if request.output_path.exists():
            raise OutputConflictError(f"database output already exists: {request.output_path}")
        temporary.replace(request.output_path)
        reference = ArtifactRef(
            path=request.output_path,
            sha256=_sha256(request.output_path),
            size_bytes=request.output_path.stat().st_size,
            kind="sqlite",
        )
        return DatabaseArtifact(
            database=reference,
            release_spec=request.release_spec,
            verification_report=report,
        )
    finally:
        if temporary.exists():
            temporary.unlink()
