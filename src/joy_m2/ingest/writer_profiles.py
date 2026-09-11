"""Private deterministic primitives for the Task 9C candidate writer."""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys

from joy_m2.errors import InputFormatError


BASELINE_SHA256 = "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
BASELINE_SIZE_BYTES = 9_363_456
FROZEN_SQLITE_HEADER_VERSION = 3_050_004
CHECK_NAMES = (
    "candidate_directory", "manifest_contract", "preflight_approval_binding",
    "filesystem_closure", "sha256sums_closure", "artifact_references",
    "rollback_contract", "image_projection", "sqlite_readability",
    "sqlite_integrity", "sqlite_foreign_keys", "sqlite_schema",
    "sqlite_projection", "baseline_preservation", "count_closure",
    "publication_boundary",
)
TASK9_SCHEMA_SQL = (
    """CREATE TABLE task9_import_batches_v1 (
        batch_id TEXT PRIMARY KEY,
        target_release_version TEXT NOT NULL CHECK(target_release_version='V1.19'),
        candidate_database_schema TEXT NOT NULL CHECK(candidate_database_schema='task9-v119-candidate-v1'),
        preflight_sha256 TEXT NOT NULL,
        manifest_sha256 TEXT NOT NULL,
        approval_statement TEXT NOT NULL,
        baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.18'),
        baseline_database_sha256 TEXT NOT NULL,
        baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=497),
        candidate_count INTEGER NOT NULL CHECK(candidate_count>=0),
        projected_question_count INTEGER NOT NULL CHECK(projected_question_count=baseline_question_count+candidate_count),
        record_status TEXT NOT NULL CHECK(record_status='candidate')
    )""",
    """CREATE TABLE task9_import_candidates_v1 (
        batch_id TEXT NOT NULL REFERENCES task9_import_batches_v1(batch_id),
        candidate_order INTEGER NOT NULL CHECK(candidate_order>=0),
        proposed_question_id TEXT NOT NULL,
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
        image_paths_json TEXT NOT NULL,
        image_sha256s_json TEXT NOT NULL,
        image_roles_json TEXT NOT NULL,
        primary_type TEXT NOT NULL,
        tags_json TEXT NOT NULL,
        tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
        difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5 OR difficulty_level IS NULL),
        difficulty_status TEXT NOT NULL CHECK(difficulty_status IN ('source_provided','proposed','missing')),
        enrichment_status TEXT NOT NULL CHECK(enrichment_status IN ('complete','incomplete')),
        candidate_image_paths_json TEXT NOT NULL,
        record_status TEXT NOT NULL CHECK(record_status='candidate'),
        selectable INTEGER NOT NULL CHECK(selectable=0),
        PRIMARY KEY(batch_id, proposed_question_id),
        UNIQUE(batch_id, candidate_order)
    )""",
    """CREATE TABLE task9_import_images_v1 (
        batch_id TEXT NOT NULL,
        proposed_question_id TEXT NOT NULL,
        image_order INTEGER NOT NULL CHECK(image_order>=0),
        source_relative_path TEXT NOT NULL,
        candidate_relative_path TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        size_bytes INTEGER NOT NULL CHECK(size_bytes>=0),
        kind TEXT NOT NULL CHECK(kind='image'),
        role TEXT NOT NULL,
        PRIMARY KEY(batch_id, proposed_question_id, image_order),
        FOREIGN KEY(batch_id, proposed_question_id)
            REFERENCES task9_import_candidates_v1(batch_id, proposed_question_id)
    )""",
    """CREATE TABLE task9_import_taxonomy_v1 (
        batch_id TEXT NOT NULL REFERENCES task9_import_batches_v1(batch_id),
        taxonomy_kind TEXT NOT NULL CHECK(taxonomy_kind IN ('primary_type','tag')),
        value TEXT NOT NULL,
        sort_order INTEGER NOT NULL CHECK(sort_order>=1),
        PRIMARY KEY(batch_id, taxonomy_kind, value),
        UNIQUE(batch_id, taxonomy_kind, sort_order)
    )""",
    """CREATE VIEW task9_candidate_questions_v1 AS
    SELECT *
    FROM task9_import_candidates_v1
    ORDER BY batch_id, candidate_order""",
)
_SHA256 = re.compile(r"[0-9a-f]{64}")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


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


def relative_path(value: object) -> str:
    if type(value) is not str or not value or value == "." or "\x00" in value:
        raise InputFormatError("artifact path must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute() or "\\" in value or path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        raise InputFormatError("artifact path must be canonical and relative")
    return value


def is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def normalized_sql(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().rstrip(";")


def atomic_rename_no_replace(source: Path, destination: Path) -> None:
    """Atomically rename one directory while refusing an existing destination."""
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        rename = library.renamex_np
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        rename.restype = ctypes.c_int
        result = rename(source_bytes, destination_bytes, 0x00000004)
    elif sys.platform.startswith("linux") and hasattr(library, "renameat2"):
        rename = library.renameat2
        rename.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        rename.restype = ctypes.c_int
        result = rename(-100, source_bytes, -100, destination_bytes, 0x00000001)
    elif os.name == "nt":
        os.rename(source, destination)
        return
    else:
        raise OSError(
            errno.ENOTSUP,
            "atomic no-replace directory rename is unavailable",
            str(destination),
        )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))
