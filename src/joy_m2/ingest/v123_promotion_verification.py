"""Independent read-only verifier for Task 13 V1.23 promotion trees."""

from __future__ import annotations

from contextlib import closing
from dataclasses import fields
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sqlite3

from joy_m2.config import PipelineConfig
from joy_m2.errors import InputFormatError, InputMissingError, PipelineError
from joy_m2.models import VerificationCheck, VerificationReport

from .v123_models import V123CandidateVerificationRequest
from .v123_promotion_models import V123PromotionContract, V123PromotionVerificationRequest
from .v123_verification import verify_v123_candidate


__all__ = ("verify_v123_promotion",)

BASELINE_SHA256 = "a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0"
BASELINE_RELEASE_DIGEST = "89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b"
BASELINE_SIZE = 10_510_336
BASELINE_MANIFEST_SHA256 = "441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b"
BASELINE_MANIFEST_SIZE = 7_915
CANDIDATE_DIGEST = "c5c51df58d64349d58bd71469fe67a72cced56e77369126d6fec66bb2fcc955a"
CANDIDATE_SHA256 = "b7e2247e004cc4c91c339693de4f106edef11bb7067e34b52887547a8006cb01"
CANDIDATE_MANIFEST_SHA256 = "febe70a572b82783bf6199679bf1a2024294d98b44b4fbe047a2349a3830a076"
CANDIDATE_SIZE = 10_764_288
CANDIDATE_MANIFEST_SIZE = 5_664
CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "candidate_binding", "manifest_contract", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v122_preservation", "batch_ledger_closure",
    "promotion_projection", "formal_query", "count_closure",
    "provenance_closure", "deterministic_identity", "publication_boundary",
)
_ASCII_SPACE = re.compile(r"[ \t\r\n\f\v]+")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_CONTRACT_VALUES = {
    "profile": "V1.23",
    "release_manifest_schema": "task13-v123-formal-manifest-v1",
    "formal_database_schema": "task13-v123-formal-v1",
    "promotion_identity_schema": "task13-v123-promotion-identity-v1",
    "rollback_schema": "task13-v123-formal-rollback-v1",
    "expected_user_version": 123,
    "database_filename": "Joy_M2_Complete_Question_DB_V1_23.sqlite3",
    "manifest_filename": "manifest.json",
    "sha256s_filename": "SHA256SUMS.txt",
    "rollback_filename": "rollback.json",
    "image_root": "images/sha256",
    "promoted_table": "task13_v123_promoted_questions_v1",
    "promotion_table": "task13_v123_promotion_v1",
    "formal_view": "formal_complete_questions_v123",
}

_PROMOTION_TABLE_SQL = """CREATE TABLE task13_v123_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.23'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task13-v123-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='append-only-multi-batch-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.22'),
    baseline_database_sha256 TEXT NOT NULL CHECK(baseline_database_sha256='a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0'),
    baseline_release_digest TEXT NOT NULL CHECK(baseline_release_digest='89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=639),
    candidate_digest TEXT NOT NULL CHECK(candidate_digest='c5c51df58d64349d58bd71469fe67a72cced56e77369126d6fec66bb2fcc955a'),
    candidate_database_sha256 TEXT NOT NULL CHECK(candidate_database_sha256='b7e2247e004cc4c91c339693de4f106edef11bb7067e34b52887547a8006cb01'),
    candidate_database_size INTEGER NOT NULL CHECK(candidate_database_size=10330112),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(candidate_manifest_sha256='febe70a572b82783bf6199679bf1a2024294d98b44b4fbe047a2349a3830a076'),
    candidate_manifest_size INTEGER NOT NULL CHECK(candidate_manifest_size=6851),
    accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=3),
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=38),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=677)
)"""

_PROMOTED_TABLE_SQL = """CREATE TABLE task13_v123_promoted_questions_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 3),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order>=0),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 640 AND 677),
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
        REFERENCES task13_v123_batch_ledger_v1(batch_ordinal,batch_id)
)"""

_FORMAL_VIEW_SQL = """CREATE VIEW formal_complete_questions_v123 AS
SELECT * FROM formal_complete_questions_v122
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task13_v123_promoted' AS authority_kind,
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
FROM task13_v123_promoted_questions_v1 AS p
ORDER BY formal_order"""

_METADATA_DELTA = {
    "release_version": "V1.23",
    "baseline_version": "V1.22",
    "baseline_sqlite_sha256": BASELINE_SHA256,
    "release_model": "append-only-multi-batch-promotion",
    "schema_version": "task13-v123-formal-v1",
    "formal_question_count": "677",
    "task13_baseline_release_digest": BASELINE_RELEASE_DIGEST,
    "task13_candidate_digest": CANDIDATE_DIGEST,
    "task13_candidate_sqlite_sha256": CANDIDATE_SHA256,
    "task13_candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
    "task13_accepted_batch_count": "3",
    "task13_promoted_questions": "38",
}


def _canonical_json_file_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalize_sql(value: str) -> str:
    result = _ASCII_SPACE.sub(" ", value).strip(" ")
    return result[:-1].rstrip(" ") if result.endswith(";") else result


def _quoted(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _sqlite_value(value: object) -> object:
    if value is None or type(value) in {int, str}:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is bytes:
        return {"blob_hex": value.hex()}
    raise InputFormatError("SQLite contains an unsupported value")


def _sqlite_semantic_payload(path: Path, formal_view: str) -> dict[str, object]:
    uri = f"file:{path.resolve()}?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as database:
        schema = [
            {
                "type": row[0], "name": row[1], "table_name": row[2],
                "sql": None if row[3] is None else _normalize_sql(row[3]),
            }
            for row in database.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
            )
        ]
        tables = [
            row[0] for row in database.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        relations = []
        for name in tables + [formal_view]:
            info = tuple(database.execute(f"PRAGMA table_info({_quoted(name)})"))
            if not info:
                raise InputFormatError(f"SQLite relation is missing: {name}")
            columns = [row[1] for row in info]
            primary = [
                row[1] for row in sorted(
                    (row for row in info if row[5]), key=lambda row: row[5]
                )
            ]
            order_columns = ["formal_order"] if name == formal_view else primary or columns
            order = ",".join(_quoted(column) for column in order_columns)
            rows = [
                [_sqlite_value(item) for item in row]
                for row in database.execute(
                    f"SELECT * FROM {_quoted(name)} ORDER BY {order}"
                )
            ]
            relations.append({"name": name, "columns": columns, "rows": rows})
        user_version = database.execute("PRAGMA user_version").fetchone()[0]
    return {
        "schema_version": "task13-v123-sqlite-semantic-v1",
        "user_version": user_version,
        "schema_objects": schema,
        "relations": relations,
    }


def _baseline_projection(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "release_version": "V1.22", "question_count": 639,
        "release_digest": BASELINE_RELEASE_DIGEST,
        "database_schema": "task12-v122-formal-v1",
        "sqlite": {"kind": "sqlite", "sha256": BASELINE_SHA256, "size_bytes": BASELINE_SIZE},
        "manifest": {
            "kind": "manifest", "sha256": BASELINE_MANIFEST_SHA256,
            "size_bytes": BASELINE_MANIFEST_SIZE,
        },
    }


def _candidate_projection() -> dict[str, object]:
    return {
        "generation": 3, "release_version": "V1.23", "release_status": "candidate",
        "database_schema": "task13-v123-candidate-v1",
        "candidate_digest": CANDIDATE_DIGEST,
        "sqlite": {"kind": "sqlite", "sha256": CANDIDATE_SHA256, "size_bytes": CANDIDATE_SIZE},
        "manifest": {"kind": "manifest", "sha256": CANDIDATE_MANIFEST_SHA256, "size_bytes": CANDIDATE_MANIFEST_SIZE},
    }


def verify_v123_promotion(request: V123PromotionVerificationRequest, config: PipelineConfig) -> VerificationReport:
    return None
