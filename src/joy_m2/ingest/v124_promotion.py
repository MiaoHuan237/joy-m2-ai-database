"""Deterministic Task 14 V1.24 promotion builder and publication gate."""

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
import stat
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

from .v124_promotion_models import (
    V124ReleasePromotionApproval,
    V124PromotionArtifacts,
    V124PromotionBuildRequest,
    V124PromotionContract,
    V124PromotionVerificationRequest,
    V124PublicationRequest,
)
from .vector_ch12_delegated_models import ChapterVerificationRequest
from .writer_profiles import atomic_rename_no_replace
from .v124_verification import verify_chapter_candidate


BASELINE_SHA256 = "28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd"
BASELINE_RELEASE_DIGEST = "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc"
BASELINE_SIZE = 10_928_128
BASELINE_MANIFEST_SHA256 = "54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498"
BASELINE_MANIFEST_SIZE = 6_728
CANDIDATE_DIGEST = "3f14589da452207d0088cd44689aded7ffbadea0768a85d808a67ae526a5f3ab"
CANDIDATE_SHA256 = "93acb2b4c333c4cb881c327389569898ab110ab2f436f00f1d40586e0ed4f8a0"
CANDIDATE_MANIFEST_SHA256 = "34cd37e27370a72e332d7047d9699d3910d853e1276132ce33ec26df4786de94"
CANDIDATE_SIZE = 11_378_688
CANDIDATE_MANIFEST_SIZE = 676_520

PROMOTION_TABLE_SQL = """CREATE TABLE task14_v124_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.24'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task14-v124-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='append-only-multi-batch-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.23'),
    baseline_database_sha256 TEXT NOT NULL CHECK(baseline_database_sha256='28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd'),
    baseline_release_digest TEXT NOT NULL CHECK(baseline_release_digest='84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=677),
    candidate_digest TEXT NOT NULL CHECK(candidate_digest='3f14589da452207d0088cd44689aded7ffbadea0768a85d808a67ae526a5f3ab'),
    candidate_database_sha256 TEXT NOT NULL CHECK(candidate_database_sha256='93acb2b4c333c4cb881c327389569898ab110ab2f436f00f1d40586e0ed4f8a0'),
    candidate_database_size INTEGER NOT NULL CHECK(candidate_database_size=11378688),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(candidate_manifest_sha256='34cd37e27370a72e332d7047d9699d3910d853e1276132ce33ec26df4786de94'),
    candidate_manifest_size INTEGER NOT NULL CHECK(candidate_manifest_size=676520),
    accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=8),
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=114),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=791)
)"""

PROMOTED_TABLE_SQL = """CREATE TABLE task14_v124_promoted_questions_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 8),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order>=0),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 678 AND 791),
    question_id TEXT NOT NULL UNIQUE,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL,
    normalized_text_sha256 TEXT NOT NULL,
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
    UNIQUE(batch_ordinal,batch_candidate_order),
    FOREIGN KEY(batch_ordinal,batch_id)
        REFERENCES task14_v124_batch_ledger_v1(batch_ordinal,batch_id)
)"""

FORMAL_VIEW_SQL = """CREATE VIEW formal_complete_questions_v124 AS
SELECT * FROM formal_complete_questions_v123
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task14_v124_promoted' AS authority_kind,
    p.batch_id,
    p.batch_candidate_order AS candidate_order,
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
FROM task14_v124_promoted_questions_v1 AS p
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
    uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
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
        "schema_version": "task14-v124-sqlite-semantic-v1",
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


def _candidate_manifest(request: ChapterVerificationRequest) -> tuple[dict[str, object], bytes]:
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
    request: V124PromotionBuildRequest,
    config: PipelineConfig,
) -> tuple[Path, Path, dict[str, object]]:
    if not _reconstructs_exactly(request, V124PromotionBuildRequest):
        raise PipelineError("request must be an exact valid V124PromotionBuildRequest")
    if not _reconstructs_exactly(config, PipelineConfig):
        raise PipelineError("config must be an exact valid PipelineConfig")
    candidate = request.candidate
    if not _reconstructs_exactly(candidate, ChapterVerificationRequest):
        raise PromotionError("candidate authority carrier is invalid")
    try:
        candidate_report = verify_chapter_candidate(candidate, config)
    except PipelineError as error:
        raise PromotionError("Task 10A candidate authority is invalid") from error
    if candidate_report.status != "PASS" or not all(check.passed for check in candidate_report.checks):
        raise PromotionError("Task 10A candidate verification did not pass")
    if len(candidate_report.checks) != 24 or len(candidate.approved_batches) != 8:
        raise PromotionError("candidate is outside the exact approved Task 14 authority")
    expected_batches = tuple(
        (f"JOY-M2-OSM-M2B12-VECTOR-20261023-001-S{i:02}", count)
        for i,count in enumerate((16,14,4,14,11,32,20,3),1)
    )
    exact = (
        tuple(
            (batch.approval.batch_id, len(batch.preflight_result.candidates))
            for batch in candidate.approved_batches
        ) == expected_batches,
        sum(len(batch.preflight_result.candidates) for batch in candidate.approved_batches) == 114,
        candidate.approved_batches[0].preflight_result.effective_state.baseline_database.sha256
        == BASELINE_SHA256,
    )
    if not all(exact):
        raise PromotionError("candidate is outside the exact approved Task 14 authority")
    manifest, manifest_bytes = _candidate_manifest(candidate)
    database = candidate.candidate_dir / candidate.contract.database_filename
    if (
        not database.is_file()
        or database.is_symlink()
        or _sha256_file(database) != CANDIDATE_SHA256
        or _sha256_bytes(manifest_bytes) != CANDIDATE_MANIFEST_SHA256
        or database.stat().st_size != CANDIDATE_SIZE
        or len(manifest_bytes) != CANDIDATE_MANIFEST_SIZE
        or manifest.get("candidate_digest") != CANDIDATE_DIGEST
        or manifest.get("counts") != {
            "baseline_question_count": 677,
            "batch_count": 8,
            "new_candidate_count": 114,
            "projected_question_count": 791,
        }
    ):
        raise PromotionError("candidate artifact identity does not match Task 14 authority")
    declared_output = request.output_dir
    try:
        if _has_symlink_component(declared_output):
            raise PipelineError("promotion output path contains a symlink")
        resolved_output = declared_output.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise PipelineError("promotion output path is invalid") from error
    if declared_output != resolved_output:
        raise PipelineError("promotion output path must preserve lexical identity")
    output = config.require_staging_output(declared_output)
    if output == config.staging_root:
        raise PipelineError("promotion output must be a strict staging descendant")
    if output.exists():
        raise OutputConflictError("promotion output already exists")
    candidate_root = candidate.candidate_dir.resolve(strict=False)
    candidate_generation_roots = tuple(
        config.repo_root / name for name in (
            "data/staging/task9c-v119-candidate",
            "data/staging/task9c-v119-real-0918-interval-candidate",
            "data/staging/task10a-v120-real-candidate-000001-hkdse-2012",
            "data/staging/task10a-v120-real-candidate-000002-hkdse-2013",
            "data/staging/task10a-v120-real-candidate-000003-hkdse-2014",
            "data/staging/task11-v121-hkdse-2015",
            "data/staging/task11-v121-hkdse-2016",
            "data/staging/task11-v121-hkdse-2017",
            "data/staging/task11-v121-hkdse-2018",
            "data/staging/task12-v122-hkdse-2019",
            "data/staging/task12-v122-hkdse-2020",
            "data/staging/task12-v122-hkdse-2021",
            "data/staging/task12-v122-hkdse-2022",
            "data/staging/task13-v123-hkdse-2023",
            "data/staging/task13-v123-hkdse-2025",
            "data/staging/task10b-hkdse-2019",
            "data/staging/task10b-hkdse-2020",
            "data/staging/task10b-hkdse-2021",
            "data/staging/task10b-hkdse-2022",
            "data/staging/auto-ingestion/candidates",
            "data/staging/auto-ingestion/packages",
            "data/staging/auto-ingestion/receipts",
            "data/staging/task10b-hkdse-2023",
            "data/staging/task10b-hkdse-2024",
            "data/staging/task10b-hkdse-2025",
            "data/staging/oxford-c1-review-20261014",
        )
    )
    protected_roots = [
        *(config.releases_root / f"V1.{version}" for version in range(18, 25)),
        candidate_root,
        *candidate_generation_roots,
        *config.staging_root.glob("vector-ch12-*"),
        *(batch.package_root for batch in candidate.approved_batches),
    ]
    for protected in (path.resolve(strict=False) for path in protected_roots):
        if output == protected or output.is_relative_to(protected) or protected.is_relative_to(output):
            raise PipelineError("promotion paths must not overlap inputs")
    return output, database, manifest


def _populate_database(path: Path, request: V124PromotionBuildRequest) -> None:
    with closing(sqlite3.connect(path)) as database:
        database.execute("PRAGMA foreign_keys=ON")
        database.execute("BEGIN IMMEDIATE")
        try:
            database.execute(PROMOTION_TABLE_SQL)
            database.execute(PROMOTED_TABLE_SQL)
            database.execute(
                "INSERT INTO task14_v124_promotion_v1 VALUES ("
                + ",".join("?" for _ in range(16)) + ")",
                (
                    "V1.24", request.contract.formal_database_schema,
                    "append-only-multi-batch-promotion", "published", "V1.23",
                    BASELINE_SHA256, BASELINE_RELEASE_DIGEST, 677,
                    CANDIDATE_DIGEST, CANDIDATE_SHA256, CANDIDATE_SIZE,
                    CANDIDATE_MANIFEST_SHA256, CANDIDATE_MANIFEST_SIZE,
                    8, 114, 791,
                ),
            )
            rows = tuple(
                database.execute(
                    "SELECT * FROM task14_v124_candidates_v1 ORDER BY aggregate_order"
                )
            )
            if len(rows) != 114 or tuple(row[3] for row in rows) != tuple(range(678, 792)):
                raise PromotionError("candidate row closure is invalid")
            baseline_ids = {
                row[0] for row in database.execute(
                    "SELECT question_id FROM formal_complete_questions_v123"
                )
            }
            if any(row[4] in baseline_ids for row in rows):
                raise PromotionError("candidate question ID collides with V1.23")
            for row in rows:
                database.execute(
                    "INSERT INTO task14_v124_promoted_questions_v1 VALUES ("
                    + ",".join("?" for _ in range(32))
                    + ")",
                    (*row[:30], "published", 1),
                )
            database.execute(FORMAL_VIEW_SQL)
            metadata = {
                "release_version": "V1.24",
                "baseline_version": "V1.23",
                "baseline_sqlite_sha256": BASELINE_SHA256,
                "release_model": "append-only-multi-batch-promotion",
                "schema_version": request.contract.formal_database_schema,
                "formal_question_count": "791",
                "task14_baseline_release_digest": BASELINE_RELEASE_DIGEST,
                "task14_candidate_digest": CANDIDATE_DIGEST,
                "task14_candidate_sqlite_sha256": CANDIDATE_SHA256,
                "task14_candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
                "task14_accepted_batch_count": "8",
                "task14_promoted_questions": "114",
            }
            for key, value in metadata.items():
                database.execute(
                    "INSERT INTO release_metadata_v2(key,value) VALUES (?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, value),
                )
            database.execute("PRAGMA user_version=124")
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
    request: V124PromotionBuildRequest,
    database_artifact: dict[str, object],
    semantic_sha256: str,
    images: list[dict[str, object]],
) -> dict[str, object]:
    manifest, _ = _candidate_manifest(request.candidate)
    contract = {
        field.name: getattr(request.contract, field.name)
        for field in fields(V124PromotionContract)
    }
    return {
        "schema_version": request.contract.promotion_identity_schema,
        "release_version": "V1.24",
        "contract": contract,
        "baseline": _baseline_projection(manifest),
        "candidate": _candidate_projection(manifest),
        "batch_ledger": manifest["batch_ledger"],
        "batch_authority_artifacts": manifest["batch_authority_artifacts"],
        "counts": {
            "baseline_question_count": 677,
            "accepted_batch_count": 8,
            "promoted_question_count": 114,
            "formal_question_count": 791,
        },
        "formal_sqlite_sha256": database_artifact["sha256"],
        "formal_sqlite_size_bytes": database_artifact["size_bytes"],
        "formal_sqlite_semantic_sha256": semantic_sha256,
        "images": images,
        "rollback_action": "remove_release_tree_if_release_digest_matches",
    }


def _baseline_projection(manifest: dict[str, object]) -> dict[str, object]:
    value = manifest["baseline"]
    return {
        "release_version": "V1.23",
        "question_count": 677,
        "release_digest": BASELINE_RELEASE_DIGEST,
        "database_schema": "task13-v123-formal-v1",
        "sqlite": {
            "kind": "sqlite", "sha256": BASELINE_SHA256, "size_bytes": BASELINE_SIZE,
        },
        "manifest": {
            "kind": "manifest",
            "sha256": BASELINE_MANIFEST_SHA256,
            "size_bytes": BASELINE_MANIFEST_SIZE,
        },
    }


def _candidate_projection(manifest: dict[str, object]) -> dict[str, object]:
    return {
        "generation": 8,
        "release_version": "V1.24",
        "release_status": "candidate",
        "database_schema": "task14-v124-ch12-candidate-v1",
        "candidate_digest": CANDIDATE_DIGEST,
        "sqlite": {"kind": "sqlite", "sha256": CANDIDATE_SHA256, "size_bytes": CANDIDATE_SIZE},
        "manifest": {
            "kind": "manifest", "sha256": CANDIDATE_MANIFEST_SHA256,
            "size_bytes": CANDIDATE_MANIFEST_SIZE,
        },
    }


def _write_release_artifacts(
    root: Path,
    request: V124PromotionBuildRequest,
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
        "release_version": "V1.24",
        "release_digest": release_digest,
        "protected_baseline": {
            "release_version": "V1.23",
            "sqlite_sha256": BASELINE_SHA256,
            "question_count": 677,
            "release_digest": BASELINE_RELEASE_DIGEST,
        },
        "candidate_digest": CANDIDATE_DIGEST,
        "release_artifacts": paths,
    }
    rollback_path = root / contract.rollback_filename
    rollback_path.write_bytes(_canonical_json_file_bytes(rollback))
    rollback_artifact = _artifact(contract.rollback_filename, rollback_path, "rollback")
    manifest = {
        "schema_version": contract.release_manifest_schema,
        "release_version": "V1.24",
        "release_status": "published",
        "release_model": "append-only-multi-batch-promotion",
        "database_schema": contract.formal_database_schema,
        "baseline": _baseline_projection(candidate_manifest),
        "candidate": _candidate_projection(candidate_manifest),
        "batch_ledger": candidate_manifest["batch_ledger"],
        "batch_authority_artifacts": candidate_manifest["batch_authority_artifacts"],
        "counts": {
            "baseline_question_count": 677,
            "accepted_batch_count": 8,
            "promoted_question_count": 114,
            "formal_question_count": 791,
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
            "authority": "verify_v124_promotion",
            "check_names": [
                "release_directory", "promotion_contract", "candidate_verification",
                "candidate_binding", "manifest_contract", "filesystem_closure",
                "sha256sums_closure", "artifact_references", "rollback_contract",
                "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
                "sqlite_schema", "v123_preservation", "batch_ledger_closure",
                "promotion_projection", "formal_query", "count_closure",
                "provenance_closure", "deterministic_identity",
                "publication_boundary", "image_projection",
            ],
            "required_status": "PASS",
        },
        "promotion": {
            "gate": "FINAL",
            "release_digest": release_digest,
            "required_statement": f"USER APPROVED RELEASE PROMOTION V1.24 {release_digest}",
            "formal_target": "releases/V1.24",
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


def _result(root: Path, contract: V124PromotionContract, report) -> V124PromotionArtifacts:
    manifest = json.loads((root / contract.manifest_filename).read_text(encoding="utf-8"))
    images = tuple(
        ArtifactRef(
            root / item["relative_path"], item["sha256"], item["size_bytes"], "image"
        )
        for item in manifest["images"]
    )
    return V124PromotionArtifacts(
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
    approval: V124ReleasePromotionApproval,
    contract: V124PromotionContract,
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
        == f"USER APPROVED RELEASE PROMOTION V1.24 {release_digest}"
    )


def _has_symlink_component(path: Path) -> bool:
    try:
        return any(component.is_symlink() for component in (path, *path.parents))
    except (OSError, RuntimeError):
        return True


def _directory_identity(path: Path) -> tuple[int, int] | None:
    info = path.lstat()
    return (info.st_dev, info.st_ino) if stat.S_ISDIR(info.st_mode) else None


def _cleanup_owned_directory(path: Path, owner: tuple[int, int], fingerprint=None) -> None:
    try:
        current = _directory_identity(path)
    except FileNotFoundError:
        return
    if current != owner or (fingerprint is not None and _tree_fingerprint(path) != fingerprint):
        raise PromotionError("failed output cannot be cleaned safely: ownership or bytes changed")
    # Claim the object into a private, exclusive namespace before deleting it.
    # A concurrent writer may replace the public path during the fingerprint
    # read or rename; checking the moved object prevents deleting that writer's
    # directory. Never overwrite a new occupant when restoring rejected state.
    quarantine = Path(tempfile.mkdtemp(prefix=f".{path.name}-cleanup-", dir=path.parent))
    claimed = quarantine / "owned"
    try:
        path.rename(claimed)
        if (_directory_identity(claimed) != owner
                or (fingerprint is not None and _tree_fingerprint(claimed) != fingerprint)
                or _directory_identity(claimed) != owner):
            raise PromotionError("failed output cannot be cleaned safely: ownership or bytes changed")
        shutil.rmtree(claimed)
    except Exception:
        if claimed.exists() or claimed.is_symlink():
            try:
                atomic_rename_no_replace(claimed, path)
            except Exception:
                # Keep the claimed evidence if another writer now owns path.
                # This private directory must not be recursively cleaned.
                raise PromotionError(f"failed output retained for manual recovery: {claimed}")
        raise
    finally:
        if not claimed.exists() and not claimed.is_symlink():
            quarantine.rmdir()


def build_v124_promotion(
    request: V124PromotionBuildRequest,
    config: PipelineConfig,
) -> V124PromotionArtifacts:
    output, candidate_database, candidate_manifest = _validate_build_request(request, config)
    output.parent.mkdir(parents=True, exist_ok=True)
    private = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    owner = _directory_identity(private)
    published_fingerprint = None
    renamed = False
    try:
        database = private / request.contract.database_filename
        shutil.copyfile(candidate_database, database)
        _populate_database(database, request)
        _write_release_artifacts(private, request, candidate_manifest)
        from .v124_promotion_verification import verify_v124_promotion

        report = verify_v124_promotion(
            V124PromotionVerificationRequest(private, request.candidate, request.contract),
            config,
        )
        if report.status != "PASS" or not all(check.passed for check in report.checks):
            raise PromotionError("staging promotion verification failed")
        published_fingerprint = _tree_fingerprint(private)
        if _directory_identity(private) != owner:
            raise PromotionError("private staging ownership changed")
        atomic_rename_no_replace(private, output)
        renamed = True
        report = verify_v124_promotion(
            V124PromotionVerificationRequest(output, request.candidate, request.contract),
            config,
        )
        if (_directory_identity(output) != owner or report.status != "PASS"
                or not all(check.passed for check in report.checks)):
            raise PromotionError("published staging promotion verification failed")
        return _result(output, request.contract, report)
    except Exception:
        _cleanup_owned_directory(private, owner)
        if renamed and output.exists() and published_fingerprint is not None:
            _cleanup_owned_directory(output, owner, published_fingerprint)
        raise



def publish_v124_release(
    request: V124PublicationRequest,
    config: PipelineConfig,
) -> V124PromotionArtifacts:
    if not _reconstructs_exactly(request, V124PublicationRequest):
        raise PipelineError("request must be an exact valid V124PublicationRequest")
    if not _reconstructs_exactly(config, PipelineConfig):
        raise PipelineError("config must be an exact valid PipelineConfig")
    if not _reconstructs_exactly(request.approval, V124ReleasePromotionApproval):
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
    from .v124_promotion_verification import verify_v124_promotion

    # Bind the byte snapshot before verification, not after it. A source
    # change after PASS must never be copied into the formal namespace.
    source_fingerprint = _tree_fingerprint(source)
    source_report = verify_v124_promotion(
        V124PromotionVerificationRequest(source, request.candidate, request.contract),
        config,
    )
    if source_report.status != "PASS" or not all(
        check.passed for check in source_report.checks
    ):
        raise PromotionError("dry-run promotion verification failed")
    if not _gate_d_binds_root(source, request.approval, request.contract):
        raise PromotionError("Gate D approval does not bind this release")
    if _tree_fingerprint(source) != source_fingerprint:
        raise PromotionError("dry-run promotion changed during verification")
    lexical_releases = config.repo_root / "releases"
    try:
        if (
            _has_symlink_component(lexical_releases)
            or lexical_releases.resolve(strict=False) != config.releases_root
        ):
            raise PromotionError("formal releases root is unsafe")
    except (OSError, RuntimeError) as error:
        raise PromotionError("formal releases root is unsafe") from error
    target = config.new_formal_target("V1.24")
    target.parent.mkdir(parents=True, exist_ok=True)
    private = Path(tempfile.mkdtemp(prefix=".V1.24-publish-", dir=target.parent))
    owner = _directory_identity(private)
    renamed = False
    try:
        shutil.copytree(source, private, dirs_exist_ok=True)
        if _tree_fingerprint(private) != source_fingerprint:
            raise PromotionError("private publication copy is not byte-identical")
        if not _gate_d_binds_root(private, request.approval, request.contract):
            raise PromotionError("Gate D approval does not bind the private snapshot")
        if _directory_identity(private) != owner:
            raise PromotionError("private publication ownership changed")
        atomic_rename_no_replace(private, target)
        renamed = True
        final_report = verify_v124_promotion(
            V124PromotionVerificationRequest(target, request.candidate, request.contract),
            config,
        )
        if (
            _directory_identity(target) != owner
            or final_report.status != "PASS"
            or not all(check.passed for check in final_report.checks)
            or not _gate_d_binds_root(target, request.approval, request.contract)
        ):
            raise PromotionError("formal V1.24 post-publication verification failed")
        result = _result(target, request.contract, final_report)
        if result.release_digest != request.approval.release_digest:
            raise PromotionError("formal V1.24 result is not bound to final approval")
        return result
    except Exception as error:
        _cleanup_owned_directory(private, owner)
        if renamed and target.exists():
            _cleanup_owned_directory(target, owner, source_fingerprint)
        if isinstance(error, PipelineError):
            raise
        raise PromotionError("formal V1.24 publication failed") from error
