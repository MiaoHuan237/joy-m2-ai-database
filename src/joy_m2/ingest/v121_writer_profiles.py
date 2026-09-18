"""Private deterministic constants and pure helpers for Task 11 candidates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from joy_m2.errors import InputFormatError


BASELINE_SHA256 = "b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292"
BASELINE_SIZE_BYTES = 9_768_960
BASELINE_MANIFEST_SHA256 = "19ac2e43ded74a3f3eaf75c184b5eb231c9f1b0b152f5914cd822a321b045098"
BASELINE_MANIFEST_SIZE_BYTES = 6_643
BASELINE_RELEASE_DIGEST = "1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf"
GENESIS_DIGEST = "331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906"

CHECK_NAMES = (
    "candidate_directory", "candidate_contract", "baseline_authority",
    "batch_authority_artifacts", "parent_chain", "approval_binding",
    "preflight_reconstruction", "filesystem_closure", "sha256sums_closure",
    "artifact_references", "rollback_contract", "image_projection",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v120_preservation", "batch_ledger",
    "candidate_projection", "effective_collision_closure", "count_closure",
    "candidate_digest", "deterministic_identity", "formal_boundary",
)

TASK11_SCHEMA_SQL = (
    """CREATE TABLE task11_v121_batch_ledger_v1 (
    batch_ordinal INTEGER PRIMARY KEY CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL UNIQUE CHECK(length(batch_id) BETWEEN 1 AND 128),
    target_release_version TEXT NOT NULL CHECK(target_release_version = 'V1.21'),
    candidate_database_schema TEXT NOT NULL
        CHECK(candidate_database_schema = 'task11-v121-candidate-v1'),
    parent_candidate_digest TEXT NOT NULL
        CHECK(length(parent_candidate_digest) = 64
              AND parent_candidate_digest NOT GLOB '*[^0-9a-f]*'),
    preflight_sha256 TEXT NOT NULL UNIQUE
        CHECK(length(preflight_sha256) = 64
              AND preflight_sha256 NOT GLOB '*[^0-9a-f]*'),
    manifest_sha256 TEXT NOT NULL
        CHECK(length(manifest_sha256) = 64
              AND manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
    approval_statement TEXT NOT NULL
        CHECK(approval_statement =
              'USER APPROVED IMPORT BATCH ' || batch_id || ' ' ||
              preflight_sha256 || ' V1.21 PARENT ' ||
              parent_candidate_digest),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version = 'V1.20'),
    baseline_database_sha256 TEXT NOT NULL
        CHECK(baseline_database_sha256 =
              'b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292'),
    baseline_release_digest TEXT NOT NULL
        CHECK(baseline_release_digest =
              '1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count = 543),
    batch_candidate_count INTEGER NOT NULL CHECK(batch_candidate_count >= 0),
    cumulative_candidate_count INTEGER NOT NULL
        CHECK(cumulative_candidate_count >= batch_candidate_count),
    projected_question_count INTEGER NOT NULL
        CHECK(projected_question_count = 543 + cumulative_candidate_count),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    UNIQUE(batch_ordinal, batch_id)
)""",
    """CREATE TABLE task11_v121_candidates_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order >= 0),
    aggregate_order INTEGER NOT NULL CHECK(aggregate_order >= 544),
    proposed_question_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL,
    normalized_text_sha256 TEXT NOT NULL,
    question_text_original TEXT NOT NULL,
    question_text_zh TEXT NOT NULL,
    translation_status TEXT NOT NULL
        CHECK(translation_status IN ('source_present','ai_proposed','verified','missing')),
    translation_evidence TEXT,
    solution_original TEXT NOT NULL,
    solution_verified TEXT NOT NULL,
    answer_status TEXT NOT NULL
        CHECK(answer_status IN ('source_provided','ai_solved_verified','missing_from_source')),
    explanation_text TEXT NOT NULL,
    explanation_status TEXT NOT NULL
        CHECK(explanation_status IN ('source_present','ai_proposed','verified','missing')),
    explanation_evidence TEXT,
    image_paths_json TEXT NOT NULL,
    image_sha256s_json TEXT NOT NULL,
    image_roles_json TEXT NOT NULL,
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
    difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5
                                   OR difficulty_level IS NULL),
    difficulty_status TEXT NOT NULL
        CHECK(difficulty_status IN ('source_provided','proposed','missing')),
    enrichment_status TEXT NOT NULL
        CHECK(enrichment_status IN ('complete','incomplete')),
    candidate_image_paths_json TEXT NOT NULL,
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    selectable INTEGER NOT NULL CHECK(selectable = 0),
    PRIMARY KEY(batch_id, proposed_question_id),
    UNIQUE(proposed_question_id),
    UNIQUE(aggregate_order),
    UNIQUE(batch_ordinal, batch_candidate_order),
    UNIQUE(batch_ordinal, batch_id, proposed_question_id),
    FOREIGN KEY(batch_ordinal, batch_id)
        REFERENCES task11_v121_batch_ledger_v1(batch_ordinal, batch_id)
)""",
    """CREATE TABLE task11_v121_images_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    proposed_question_id TEXT NOT NULL,
    image_order INTEGER NOT NULL CHECK(image_order >= 0),
    source_relative_path TEXT NOT NULL,
    candidate_relative_path TEXT NOT NULL,
    sha256 TEXT NOT NULL
        CHECK(length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
    size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
    kind TEXT NOT NULL CHECK(kind = 'image'),
    role TEXT NOT NULL,
    PRIMARY KEY(batch_id, proposed_question_id, image_order),
    FOREIGN KEY(batch_ordinal, batch_id, proposed_question_id)
        REFERENCES task11_v121_candidates_v1(
            batch_ordinal, batch_id, proposed_question_id
        )
)""",
    """CREATE TABLE task11_v121_taxonomy_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    taxonomy_kind TEXT NOT NULL CHECK(taxonomy_kind IN ('primary_type','tag')),
    value TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(sort_order >= 1),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    PRIMARY KEY(batch_ordinal, batch_id, taxonomy_kind, value),
    UNIQUE(batch_ordinal, batch_id, taxonomy_kind, sort_order),
    FOREIGN KEY(batch_ordinal, batch_id)
        REFERENCES task11_v121_batch_ledger_v1(batch_ordinal, batch_id)
)""",
    """CREATE VIEW task11_candidate_questions_v121 AS
SELECT f.*
FROM formal_complete_questions_v120 AS f
UNION ALL
SELECT
    c.aggregate_order AS formal_order,
    c.proposed_question_id AS question_id,
    'task11_v121_candidate' AS authority_kind,
    c.batch_id AS batch_id,
    c.batch_candidate_order AS candidate_order,
    c.source_id,
    c.source_question_number,
    c.source_section,
    c.source_fragment_hash,
    c.normalized_text_sha256,
    c.question_text_original,
    c.question_text_zh,
    CAST(NULL AS TEXT) AS question_text_zh_reviewed,
    c.translation_status,
    c.translation_evidence,
    c.solution_original,
    c.solution_verified,
    c.answer_status,
    c.explanation_text,
    c.explanation_status,
    c.explanation_evidence,
    c.image_paths_json AS source_image_paths_json,
    c.image_sha256s_json AS source_image_sha256s_json,
    c.image_roles_json AS source_image_roles_json,
    c.primary_type,
    c.tags_json,
    c.tag_status,
    c.difficulty_level,
    c.difficulty_status,
    c.enrichment_status,
    c.candidate_image_paths_json AS formal_image_paths_json,
    c.record_status,
    c.selectable
FROM task11_v121_candidates_v1 AS c
ORDER BY formal_order""",
)

_SHA256 = re.compile(r"[0-9a-f]{64}")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_file_bytes(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def relative_path(value: object) -> str:
    if type(value) is not str or not value or value == "." or "\x00" in value:
        raise InputFormatError("artifact path must be a non-empty string")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or "\\" in value
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise InputFormatError("artifact path must be canonical and relative")
    return value


def normalized_sql(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().rstrip(";")


def image_destination(image_root: str, source_path: str, digest: str) -> str:
    relative_path(source_path)
    relative_path(image_root)
    if not is_sha256(digest):
        raise InputFormatError("image digest must be lowercase SHA-256")
    suffix = Path(source_path).suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        extension = ".jpg"
    elif suffix in {".png", ".svg"}:
        extension = suffix
    else:
        raise InputFormatError("image extension is unsupported")
    return f"{image_root}/{digest[:2]}/{digest}{extension}"
