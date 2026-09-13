"""Deterministic Task 9D V1.19 promotion builder and publication gate."""

from __future__ import annotations

from contextlib import closing
from dataclasses import fields
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import tempfile

from joy_m2.config import PipelineConfig
from joy_m2.errors import (
    InputFormatError,
    InputMissingError,
    OutputConflictError,
    PipelineError,
    PromotionError,
)
from joy_m2.models import ArtifactRef

from .promotion_models import (
    ReleasePromotionApproval,
    V119PromotionArtifacts,
    V119PromotionBuildRequest,
    V119PromotionContract,
    V119PromotionVerificationRequest,
    V119PublicationRequest,
)
from .writer_models import V119VerificationRequest
from .writer_profiles import atomic_rename_no_replace
from .writer_verification import verify_v119_candidate


BASELINE_SHA256 = "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
CANDIDATE_SHA256 = "9d30cf444e9d6686128f884d5a3cf57f4e58ce544b7933d7a0a47ec0e8212d20"
CANDIDATE_MANIFEST_SHA256 = "b2e0b4607b49f5e1e097fd036dd0614c67128976e7d282f4e2783eb092be9634"
BATCH_ID = "TASK9B-REAL-0918-INTERVAL-REPRODUCTION-001"
PREFLIGHT_SHA256 = "4aa3ff8b419a0fcca57c805d5f10f252658cb30c00f6cf1b74c95ab3009333c9"

PROMOTION_TABLE_SQL = """CREATE TABLE task9_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.19'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task9-v119-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='incremental-import-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.18'),
    baseline_database_sha256 TEXT NOT NULL CHECK(length(baseline_database_sha256)=64 AND baseline_database_sha256 NOT GLOB '*[^0-9a-f]*'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=497),
    candidate_database_sha256 TEXT NOT NULL CHECK(length(candidate_database_sha256)=64 AND candidate_database_sha256 NOT GLOB '*[^0-9a-f]*'),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(length(candidate_manifest_sha256)=64 AND candidate_manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
    batch_id TEXT NOT NULL UNIQUE,
    preflight_sha256 TEXT NOT NULL CHECK(length(preflight_sha256)=64 AND preflight_sha256 NOT GLOB '*[^0-9a-f]*'),
    import_approval_statement TEXT NOT NULL,
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=5),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=baseline_question_count+promoted_question_count AND formal_question_count=502)
)"""

PROMOTED_TABLE_SQL = """CREATE TABLE task9_promoted_questions_v1 (
    batch_id TEXT NOT NULL REFERENCES task9_promotion_v1(batch_id),
    candidate_order INTEGER NOT NULL CHECK(candidate_order BETWEEN 0 AND 4),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 498 AND 502),
    question_id TEXT NOT NULL UNIQUE,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL CHECK(length(source_fragment_hash)=64 AND source_fragment_hash NOT GLOB '*[^0-9a-f]*'),
    normalized_text_sha256 TEXT NOT NULL CHECK(length(normalized_text_sha256)=64 AND normalized_text_sha256 NOT GLOB '*[^0-9a-f]*'),
    question_text_original TEXT NOT NULL,
    question_text_zh TEXT NOT NULL,
    translation_status TEXT NOT NULL CHECK(translation_status IN ('source_present','ai_proposed','verified','missing')),
    translation_evidence TEXT,
    solution_original TEXT NOT NULL,
    solution_verified TEXT NOT NULL,
    answer_status TEXT NOT NULL CHECK(answer_status IN ('source_provided','ai_solved_verified','missing_from_source')),
    explanation_text TEXT NOT NULL,
    explanation_status TEXT NOT NULL CHECK(explanation_status IN ('source_present','ai_proposed','verified','missing')),
    explanation_evidence TEXT,
    source_image_paths_json TEXT NOT NULL,
    source_image_sha256s_json TEXT NOT NULL,
    source_image_roles_json TEXT NOT NULL,
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
    difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5 OR difficulty_level IS NULL),
    difficulty_status TEXT NOT NULL CHECK(difficulty_status IN ('source_provided','proposed','missing')),
    enrichment_status TEXT NOT NULL CHECK(enrichment_status IN ('complete','incomplete')),
    formal_image_paths_json TEXT NOT NULL,
    record_status TEXT NOT NULL CHECK(record_status='published'),
    selectable INTEGER NOT NULL CHECK(selectable=1),
    UNIQUE(batch_id, candidate_order),
    CHECK(formal_order=498+candidate_order)
)"""

FORMAL_VIEW_SQL = """CREATE VIEW formal_complete_questions_v119 AS
SELECT
    q.source_order AS formal_order,
    q.question_id AS question_id,
    'baseline_v118' AS authority_kind,
    CAST(NULL AS TEXT) AS batch_id,
    CAST(NULL AS INTEGER) AS candidate_order,
    q.source_id AS source_id,
    q.source_question_number AS source_question_number,
    q.source_section AS source_section,
    q.source_fragment_hash AS source_fragment_hash,
    CAST(NULL AS TEXT) AS normalized_text_sha256,
    q.question_text_original AS question_text_original,
    q.question_text_zh AS question_text_zh,
    q.question_text_zh_reviewed AS question_text_zh_reviewed,
    CAST(NULL AS TEXT) AS translation_status,
    CAST(NULL AS TEXT) AS translation_evidence,
    q.solution_original AS solution_original,
    q.solution_verified AS solution_verified,
    q.answer_status AS answer_status,
    CAST(NULL AS TEXT) AS explanation_text,
    CAST(NULL AS TEXT) AS explanation_status,
    CAST(NULL AS TEXT) AS explanation_evidence,
    q.image_paths_json AS source_image_paths_json,
    CAST(NULL AS TEXT) AS source_image_sha256s_json,
    CAST(NULL AS TEXT) AS source_image_roles_json,
    q.primary_type AS primary_type,
    q.tags_json AS tags_json,
    CAST(NULL AS TEXT) AS tag_status,
    q.difficulty_level AS difficulty_level,
    CAST(NULL AS TEXT) AS difficulty_status,
    CAST(NULL AS TEXT) AS enrichment_status,
    q.image_paths_json AS formal_image_paths_json,
    q.record_status AS record_status,
    q.selectable AS selectable
FROM complete_questions_v2 AS q
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task9_promoted' AS authority_kind,
    p.batch_id,
    p.candidate_order,
    p.source_id,
    p.source_question_number,
    p.source_section,
    p.source_fragment_hash,
    p.normalized_text_sha256,
    p.question_text_original,
    p.question_text_zh,
    CAST(NULL AS TEXT) AS question_text_zh_reviewed,
    p.translation_status,
    p.translation_evidence,
    p.solution_original,
    p.solution_verified,
    p.answer_status,
    p.explanation_text,
    p.explanation_status,
    p.explanation_evidence,
    p.source_image_paths_json,
    p.source_image_sha256s_json,
    p.source_image_roles_json,
    p.primary_type,
    p.tags_json,
    p.tag_status,
    p.difficulty_level,
    p.difficulty_status,
    p.enrichment_status,
    p.formal_image_paths_json,
    p.record_status,
    p.selectable
FROM task9_promoted_questions_v1 AS p
ORDER BY formal_order"""

_ASCII_SPACE = re.compile(r"[ \t\r\n\f\v]+")


def _normalize_sql(value: str) -> str:
    normalized = _ASCII_SPACE.sub(" ", value).strip(" ")
    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip(" ")
    return normalized


def _canonical_json_file_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative_path(value: object) -> str:
    if type(value) is not str or not value or value == "." or "\x00" in value:
        raise InputFormatError("artifact path must be a non-empty canonical relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or "\\" in value
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise InputFormatError("artifact path must be a canonical relative path")
    return value


def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _sqlite_json_value(value: object) -> object:
    if value is None or type(value) in {int, str}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise InputFormatError("SQLite contains a non-finite number")
        return value
    if type(value) is bytes:
        return {"blob_hex": value.hex()}
    raise InputFormatError("SQLite contains an unsupported value")


def _sqlite_semantic_payload(path: Path, formal_view: str) -> dict[str, object]:
    uri = f"file:{path.resolve()}?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as database:
        schema_objects = [
            {
                "type": row[0],
                "name": row[1],
                "table_name": row[2],
                "sql": None if row[3] is None else _normalize_sql(row[3]),
            }
            for row in database.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
            )
        ]
        table_names = [
            row[0]
            for row in database.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        relations = []
        for name in table_names + [formal_view]:
            info = tuple(database.execute(f"PRAGMA table_info({_quoted(name)})"))
            if not info:
                raise InputFormatError(f"SQLite relation is missing: {name}")
            columns = [row[1] for row in info]
            if name == formal_view:
                order_columns = ["formal_order"]
            else:
                primary = [row[1] for row in sorted((row for row in info if row[5]), key=lambda row: row[5])]
                order_columns = primary or columns
            order = ",".join(_quoted(column) for column in order_columns)
            rows = [
                [_sqlite_json_value(value) for value in row]
                for row in database.execute(
                    f"SELECT * FROM {_quoted(name)} ORDER BY {order}"
                )
            ]
            relations.append({"name": name, "columns": columns, "rows": rows})
        user_version = database.execute("PRAGMA user_version").fetchone()[0]
    return {
        "schema_version": "task9-v119-sqlite-semantic-v1",
        "user_version": user_version,
        "schema_objects": schema_objects,
        "relations": relations,
    }


def _sqlite_semantic_sha256(path: Path, formal_view: str) -> str:
    return _sha256_bytes(_canonical_json_file_bytes(_sqlite_semantic_payload(path, formal_view)))


def _promotion_identity(payload: dict[str, object]) -> str:
    return _sha256_bytes(_canonical_json_file_bytes(payload))


def _reconstructs_exactly(value: object, expected: type) -> bool:
    if type(value) is not expected:
        return False
    try:
        return expected(
            **{field.name: getattr(value, field.name) for field in fields(expected) if field.init}
        ) == value
    except (AttributeError, OSError, PipelineError, RuntimeError, TypeError, ValueError):
        return False


def _candidate_manifest(request: V119VerificationRequest) -> tuple[dict[str, object], bytes]:
    path = request.candidate_dir / request.contract.manifest_filename
    if not path.is_file() or path.is_symlink():
        raise PromotionError("candidate manifest is missing")
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise PromotionError("candidate manifest is unreadable") from error
    if type(payload) is not dict:
        raise PromotionError("candidate manifest is invalid")
    return payload, raw


def _validate_build_request(
    request: V119PromotionBuildRequest,
    config: PipelineConfig,
) -> tuple[Path, Path, dict[str, object]]:
    if not _reconstructs_exactly(request, V119PromotionBuildRequest):
        raise PipelineError("request must be an exact valid V119PromotionBuildRequest")
    if not _reconstructs_exactly(config, PipelineConfig):
        raise PipelineError("config must be an exact valid PipelineConfig")
    candidate = request.candidate
    if not _reconstructs_exactly(candidate, V119VerificationRequest):
        raise PromotionError("candidate authority carrier is invalid")
    try:
        candidate_report = verify_v119_candidate(candidate, config)
    except PipelineError as error:
        raise PromotionError("Task 9C candidate authority is invalid") from error
    if candidate_report.status != "PASS" or not all(check.passed for check in candidate_report.checks):
        raise PromotionError("Task 9C candidate verification did not pass")
    preflight = candidate.preflight_result
    approval = candidate.approval
    exact = (
        preflight.baseline_database.sha256 == BASELINE_SHA256,
        preflight.report.before_count == 497,
        preflight.report.detected_count == 5,
        preflight.report.new_candidate_count == 5,
        preflight.report.projected_after_count == 502,
        preflight.manifest.batch_id == BATCH_ID,
        preflight.report.preflight_sha256 == PREFLIGHT_SHA256,
        approval.batch_id == BATCH_ID,
        approval.preflight_sha256 == PREFLIGHT_SHA256,
        approval.statement == f"USER APPROVED IMPORT BATCH {BATCH_ID} {PREFLIGHT_SHA256} V1.19",
        len(preflight.candidates) == 5,
    )
    if not all(exact):
        raise PromotionError("candidate is outside the exact approved Task 9D authority")
    manifest, manifest_bytes = _candidate_manifest(candidate)
    database = candidate.candidate_dir / candidate.contract.database_filename
    if (
        not database.is_file()
        or database.is_symlink()
        or _sha256_file(database) != CANDIDATE_SHA256
        or _sha256_bytes(manifest_bytes) != CANDIDATE_MANIFEST_SHA256
    ):
        raise PromotionError("candidate artifact identity does not match Task 9D authority")
    output = config.require_staging_output(request.output_dir)
    if output == config.staging_root:
        raise PipelineError("promotion output must be a strict staging descendant")
    if output.exists():
        raise OutputConflictError("promotion output already exists")
    baseline = preflight.baseline_database.path.resolve(strict=False)
    candidate_root = candidate.candidate_dir.resolve(strict=False)
    for protected in (baseline, candidate_root):
        if output == protected or output.is_relative_to(protected) or protected.is_relative_to(output):
            raise PipelineError("promotion paths must not overlap inputs")
    return output, database, manifest


def _populate_database(path: Path, request: V119PromotionBuildRequest) -> None:
    candidate = request.candidate
    approval = candidate.approval
    with closing(sqlite3.connect(path)) as database:
        database.execute("PRAGMA foreign_keys=ON")
        database.execute("BEGIN IMMEDIATE")
        try:
            database.execute(PROMOTION_TABLE_SQL)
            database.execute(PROMOTED_TABLE_SQL)
            database.execute(
                "INSERT INTO task9_promotion_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "V1.19", request.contract.formal_database_schema,
                    "incremental-import-promotion", "published", "V1.18",
                    BASELINE_SHA256, 497, CANDIDATE_SHA256,
                    CANDIDATE_MANIFEST_SHA256, BATCH_ID, PREFLIGHT_SHA256,
                    approval.statement, 5, 502,
                ),
            )
            rows = tuple(
                database.execute(
                    "SELECT * FROM task9_import_candidates_v1 ORDER BY candidate_order"
                )
            )
            if len(rows) != 5 or tuple(row[1] for row in rows) != tuple(range(5)):
                raise PromotionError("candidate row closure is invalid")
            baseline_ids = {
                row[0] for row in database.execute("SELECT question_id FROM complete_questions_v2")
            }
            if any(row[2] in baseline_ids for row in rows):
                raise PromotionError("candidate question ID collides with V1.18")
            for row in rows:
                database.execute(
                    "INSERT INTO task9_promoted_questions_v1 VALUES ("
                    + ",".join("?" for _ in range(31))
                    + ")",
                    (
                        row[0], row[1], 498 + row[1], row[2], *row[3:27],
                        row[27], "published", 1,
                    ),
                )
            database.execute(FORMAL_VIEW_SQL)
            metadata = {
                "release_version": "V1.19",
                "baseline_version": "V1.18",
                "baseline_sqlite_sha256": BASELINE_SHA256,
                "release_model": "incremental-import-promotion",
                "schema_version": request.contract.formal_database_schema,
                "task9_batch_id": BATCH_ID,
                "task9_preflight_sha256": PREFLIGHT_SHA256,
                "task9_candidate_sqlite_sha256": CANDIDATE_SHA256,
                "task9_candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
                "task9_promoted_questions": "5",
                "formal_question_count": "502",
            }
            for key, value in metadata.items():
                database.execute(
                    "INSERT INTO release_metadata_v2(key,value) VALUES (?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, value),
                )
            database.execute("PRAGMA user_version=119")
            database.commit()
        except Exception:
            database.rollback()
            raise


def _artifact(relative_path: str, path: Path, kind: str) -> dict[str, object]:
    return {
        "relative_path": relative_path,
        "sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size,
        "kind": kind,
    }


def _copy_images(
    candidate_root: Path,
    target_root: Path,
    candidate_manifest: dict[str, object],
) -> list[dict[str, object]]:
    safe_candidate_root = candidate_root.resolve(strict=True)
    declared = candidate_manifest.get("images")
    if type(declared) is not list:
        raise PromotionError("candidate image closure is invalid")
    result = []
    for item in declared:
        if type(item) is not dict:
            raise PromotionError("candidate image entry is invalid")
        relative = _relative_path(item.get("relative_path"))
        source = (safe_candidate_root / relative).resolve(strict=False)
        if (
            not source.is_relative_to(safe_candidate_root)
            or not source.is_file()
            or source.is_symlink()
        ):
            raise PromotionError("candidate image is missing or unsafe")
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        projected = _artifact(relative, target, "image")
        if (
            projected["sha256"] != item.get("sha256")
            or projected["size_bytes"] != item.get("size_bytes")
        ):
            raise PromotionError("candidate image bytes do not match authority")
        result.append(projected)
    result.sort(key=lambda item: item["relative_path"].encode("utf-8"))
    return result


def _promotion_payload(
    request: V119PromotionBuildRequest,
    database_artifact: dict[str, object],
    semantic_sha256: str,
    images: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": request.contract.promotion_identity_schema,
        "release_version": "V1.19",
        "baseline_database_sha256": BASELINE_SHA256,
        "baseline_question_count": 497,
        "candidate_database_sha256": CANDIDATE_SHA256,
        "candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
        "batch_id": BATCH_ID,
        "preflight_sha256": PREFLIGHT_SHA256,
        "import_approval_statement": request.candidate.approval.statement,
        "promoted_question_count": 5,
        "formal_question_count": 502,
        "formal_sqlite_sha256": database_artifact["sha256"],
        "formal_sqlite_semantic_sha256": semantic_sha256,
        "images": images,
    }


def _candidate_evidence(manifest: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_records": manifest.get("candidate_record_evidence"),
        "sources": manifest.get("source_evidence"),
        "answers": manifest.get("answer_evidence"),
        "teacher_notes": manifest.get("teacher_notes_evidence"),
        "common_errors": manifest.get("common_errors_evidence"),
    }


def _write_release_artifacts(
    root: Path,
    request: V119PromotionBuildRequest,
    candidate_manifest: dict[str, object],
) -> str:
    contract = request.contract
    database_path = root / contract.database_filename
    database_artifact = _artifact(contract.database_filename, database_path, "sqlite")
    semantic = _sqlite_semantic_sha256(database_path, contract.formal_view)
    images = _copy_images(request.candidate.candidate_dir, root, candidate_manifest)
    release_digest = _promotion_identity(
        _promotion_payload(request, database_artifact, semantic, images)
    )
    paths = sorted(
        [
            contract.database_filename,
            contract.manifest_filename,
            contract.sha256s_filename,
            contract.rollback_filename,
            *(item["relative_path"] for item in images),
        ],
        key=lambda value: value.encode("utf-8"),
    )
    rollback = {
        "schema_version": contract.rollback_schema,
        "action": "remove_release_tree_if_release_digest_matches",
        "release_version": "V1.19",
        "release_digest": release_digest,
        "protected_baseline": {
            "release_version": "V1.18",
            "sqlite_sha256": BASELINE_SHA256,
            "question_count": 497,
        },
        "release_artifacts": paths,
    }
    rollback_path = root / contract.rollback_filename
    rollback_path.write_bytes(_canonical_json_file_bytes(rollback))
    rollback_artifact = _artifact(contract.rollback_filename, rollback_path, "rollback")
    candidate_database_path = request.candidate.candidate_dir / request.candidate.contract.database_filename
    candidate_manifest_path = request.candidate.candidate_dir / request.candidate.contract.manifest_filename
    manifest = {
        "schema_version": contract.release_manifest_schema,
        "release_version": "V1.19",
        "release_status": "published",
        "release_model": "incremental-import-promotion",
        "database_schema": contract.formal_database_schema,
        "baseline": {
            "release_version": "V1.18",
            "schema_version": "complete-question-v1.0",
            "question_count": 497,
            "sqlite": {
                "sha256": BASELINE_SHA256,
                "size_bytes": request.candidate.preflight_result.baseline_database.size_bytes,
                "kind": "sqlite",
            },
        },
        "candidate": {
            "release_version": "V1.19",
            "database_schema": "task9-v119-candidate-v1",
            "database": {
                "sha256": _sha256_file(candidate_database_path),
                "size_bytes": candidate_database_path.stat().st_size,
                "kind": "sqlite",
            },
            "manifest": {
                "sha256": _sha256_file(candidate_manifest_path),
                "size_bytes": candidate_manifest_path.stat().st_size,
                "kind": "manifest",
            },
            "evidence": _candidate_evidence(candidate_manifest),
        },
        "import_approval": {
            "batch_id": BATCH_ID,
            "preflight_sha256": PREFLIGHT_SHA256,
            "statement": request.candidate.approval.statement,
        },
        "counts": {
            "baseline_question_count": 497,
            "promoted_question_count": 5,
            "formal_question_count": 502,
        },
        "database": {
            **database_artifact,
            "semantic_sha256": semantic,
        },
        "images": images,
        "artifacts": sorted(
            [database_artifact, rollback_artifact, *images],
            key=lambda item: item["relative_path"].encode("utf-8"),
        ),
        "verification": {
            "authority": "verify_v119_promotion",
            "check_names": [
                "release_directory", "promotion_contract", "candidate_verification",
                "manifest_contract", "authority_binding", "filesystem_closure",
                "sha256sums_closure", "artifact_references", "rollback_contract",
                "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
                "sqlite_schema", "baseline_preservation", "promotion_projection",
                "formal_query", "count_closure", "publication_boundary",
            ],
            "required_status": "PASS",
        },
        "promotion": {
            "gate": "D",
            "release_digest": release_digest,
            "required_statement": f"USER APPROVED RELEASE PROMOTION V1.19 {release_digest}",
            "formal_target": "releases/V1.19",
        },
        "rollback": rollback_artifact,
    }
    manifest_path = root / contract.manifest_filename
    manifest_path.write_bytes(_canonical_json_file_bytes(manifest))
    closure = []
    for item in sorted(
        [database_artifact["relative_path"], contract.manifest_filename, contract.rollback_filename, *(image["relative_path"] for image in images)],
        key=lambda value: value.encode("utf-8"),
    ):
        closure.append(f"{_sha256_file(root / item)}  {item}\n")
    (root / contract.sha256s_filename).write_bytes("".join(closure).encode("utf-8"))
    return release_digest


def _result(root: Path, contract: V119PromotionContract, report) -> V119PromotionArtifacts:
    manifest = json.loads((root / contract.manifest_filename).read_text(encoding="utf-8"))
    images = tuple(
        ArtifactRef(
            root / item["relative_path"], item["sha256"], item["size_bytes"], "image"
        )
        for item in manifest["images"]
    )
    return V119PromotionArtifacts(
        ArtifactRef(
            root / contract.database_filename,
            manifest["database"]["sha256"],
            manifest["database"]["size_bytes"],
            "sqlite",
        ),
        ArtifactRef(
            root / contract.manifest_filename,
            _sha256_file(root / contract.manifest_filename),
            (root / contract.manifest_filename).stat().st_size,
            "manifest",
        ),
        ArtifactRef(
            root / contract.sha256s_filename,
            _sha256_file(root / contract.sha256s_filename),
            (root / contract.sha256s_filename).stat().st_size,
            "sha256sums",
        ),
        ArtifactRef(
            root / contract.rollback_filename,
            manifest["rollback"]["sha256"],
            manifest["rollback"]["size_bytes"],
            "rollback",
        ),
        images,
        manifest["promotion"]["release_digest"],
        report,
    )


def _tree_fingerprint(root: Path) -> tuple[tuple[str, str, bytes | str], ...]:
    entries = []
    for item in sorted(root.rglob("*")):
        relative = item.relative_to(root).as_posix()
        if item.is_symlink():
            entries.append((relative, "symlink", os.readlink(item)))
        elif item.is_dir():
            entries.append((relative, "directory", b""))
        elif item.is_file():
            entries.append((relative, "file", item.read_bytes()))
        else:
            entries.append((relative, "other", b""))
    return tuple(entries)


def _gate_d_binds_root(
    root: Path,
    approval: ReleasePromotionApproval,
    contract: V119PromotionContract,
) -> bool:
    path = root / contract.manifest_filename
    if not path.is_file() or path.is_symlink():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        promotion = payload["promotion"]
        release_digest = promotion["release_digest"]
    except (OSError, UnicodeError, ValueError, RecursionError, KeyError, TypeError):
        return False
    return (
        type(release_digest) is str
        and approval.release_digest == release_digest
        and approval.statement
        == f"USER APPROVED RELEASE PROMOTION V1.19 {release_digest}"
    )


def _has_symlink_component(path: Path) -> bool:
    try:
        return any(component.is_symlink() for component in (path, *path.parents))
    except (OSError, RuntimeError):
        return True


def build_v119_promotion(
    request: V119PromotionBuildRequest,
    config: PipelineConfig,
) -> V119PromotionArtifacts:
    output, candidate_database, candidate_manifest = _validate_build_request(request, config)
    output.parent.mkdir(parents=True, exist_ok=True)
    private = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    published_fingerprint = None
    try:
        database = private / request.contract.database_filename
        shutil.copyfile(candidate_database, database)
        _populate_database(database, request)
        _write_release_artifacts(private, request, candidate_manifest)
        from .promotion_verification import verify_v119_promotion

        report = verify_v119_promotion(
            V119PromotionVerificationRequest(private, request.candidate, request.contract),
            config,
        )
        if report.status != "PASS" or not all(check.passed for check in report.checks):
            raise PromotionError("staging promotion verification failed")
        published_fingerprint = _tree_fingerprint(private)
        atomic_rename_no_replace(private, output)
        report = verify_v119_promotion(
            V119PromotionVerificationRequest(output, request.candidate, request.contract),
            config,
        )
        if report.status != "PASS" or not all(check.passed for check in report.checks):
            raise PromotionError("published staging promotion verification failed")
        return _result(output, request.contract, report)
    except Exception:
        if private.exists():
            shutil.rmtree(private)
        if output.exists() and published_fingerprint is not None:
            if _tree_fingerprint(output) == published_fingerprint:
                shutil.rmtree(output)
            else:
                raise PromotionError("failed staging output cannot be cleaned safely")
        raise


def publish_v119_release(
    request: V119PublicationRequest,
    config: PipelineConfig,
) -> V119PromotionArtifacts:
    if not _reconstructs_exactly(request, V119PublicationRequest):
        raise PipelineError("request must be an exact valid V119PublicationRequest")
    if not _reconstructs_exactly(config, PipelineConfig):
        raise PipelineError("config must be an exact valid PipelineConfig")
    if not _reconstructs_exactly(request.approval, ReleasePromotionApproval):
        raise PromotionError("Gate D approval carrier is invalid")
    declared_source = request.dry_run_dir
    try:
        if _has_symlink_component(declared_source):
            raise PromotionError("dry-run promotion root is invalid")
        resolved_source = declared_source.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise PromotionError("dry-run promotion root is invalid") from error
    if declared_source != resolved_source:
        raise PromotionError("dry-run promotion root is invalid")
    source = config.require_staging_output(declared_source)
    if source == config.staging_root or not source.is_dir() or source.is_symlink():
        raise PromotionError("dry-run promotion root is invalid")
    from .promotion_verification import verify_v119_promotion

    source_report = verify_v119_promotion(
        V119PromotionVerificationRequest(source, request.candidate, request.contract),
        config,
    )
    if source_report.status != "PASS" or not all(
        check.passed for check in source_report.checks
    ):
        raise PromotionError("dry-run promotion verification failed")
    if not _gate_d_binds_root(source, request.approval, request.contract):
        raise PromotionError("Gate D approval does not bind this release")
    target = config.new_formal_target("V1.19")
    target.parent.mkdir(parents=True, exist_ok=True)
    private = Path(tempfile.mkdtemp(prefix=".V1.19-publish-", dir=target.parent))
    source_fingerprint = _tree_fingerprint(source)
    renamed = False
    try:
        shutil.copytree(source, private, dirs_exist_ok=True)
        if _tree_fingerprint(private) != source_fingerprint:
            raise PromotionError("private publication copy is not byte-identical")
        if not _gate_d_binds_root(private, request.approval, request.contract):
            raise PromotionError("Gate D approval does not bind the private snapshot")
        atomic_rename_no_replace(private, target)
        renamed = True
        final_report = verify_v119_promotion(
            V119PromotionVerificationRequest(target, request.candidate, request.contract),
            config,
        )
        if (
            final_report.status != "PASS"
            or not all(check.passed for check in final_report.checks)
            or not _gate_d_binds_root(target, request.approval, request.contract)
        ):
            if _tree_fingerprint(target) == source_fingerprint:
                shutil.rmtree(target)
            raise PromotionError("formal V1.19 post-publication verification failed")
        result = _result(target, request.contract, final_report)
        if result.release_digest != request.approval.release_digest:
            raise PromotionError("formal V1.19 result is not bound to Gate D")
        return result
    except Exception as error:
        if private.exists():
            shutil.rmtree(private)
        if renamed and target.exists():
            if _tree_fingerprint(target) == source_fingerprint:
                shutil.rmtree(target)
            else:
                raise PromotionError(
                    "failed formal publication cannot be cleaned safely"
                ) from error
        if isinstance(error, PipelineError):
            raise
        raise PromotionError("formal V1.19 publication failed") from error
