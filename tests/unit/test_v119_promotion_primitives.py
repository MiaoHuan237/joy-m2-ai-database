"""Literal primitive oracles for the Task 9D V1.19 promotion."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest

WORKTREE = Path(__file__).resolve().parents[2]
SRC = WORKTREE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.errors import InputFormatError
import joy_m2.ingest.promotion as promotion
import joy_m2.ingest.promotion_verification as verification


PROMOTION_SQL = """CREATE TABLE task9_promotion_v1 (
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

PROMOTED_SQL = """CREATE TABLE task9_promoted_questions_v1 (
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

CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "manifest_contract", "authority_binding", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "baseline_preservation", "promotion_projection",
    "formal_query", "count_closure", "publication_boundary",
)


def _required(module, name: str):
    value = getattr(module, name, None)
    if value is None:
        raise AssertionError(f"missing Task 9D private behavior: {module.__name__}.{name}")
    return value


class PromotionSchemaOracleTests(unittest.TestCase):
    def test_exact_ddl_and_ordered_verification_names(self):
        normalize = _required(promotion, "_normalize_sql")
        self.assertEqual(normalize(_required(promotion, "PROMOTION_TABLE_SQL")), normalize(PROMOTION_SQL))
        self.assertEqual(normalize(_required(promotion, "PROMOTED_TABLE_SQL")), normalize(PROMOTED_SQL))
        self.assertEqual(normalize(_required(promotion, "FORMAL_VIEW_SQL")), normalize(FORMAL_VIEW_SQL))
        self.assertEqual(normalize(_required(verification, "_PROMOTION_SQL")), normalize(PROMOTION_SQL))
        self.assertEqual(normalize(_required(verification, "_PROMOTED_SQL")), normalize(PROMOTED_SQL))
        self.assertEqual(normalize(_required(verification, "_FORMAL_VIEW_SQL")), normalize(FORMAL_VIEW_SQL))
        self.assertEqual(_required(verification, "CHECK_NAMES"), CHECK_NAMES)

    def test_ascii_only_sql_normalization(self):
        normalize = _required(promotion, "_normalize_sql")
        self.assertEqual(normalize(" \tCREATE\nTABLE x(a TEXT);  \r\n"), "CREATE TABLE x(a TEXT)")
        self.assertEqual(normalize("SELECT\u00a0x;"), "SELECT\u00a0x")


class PromotionIdentityPrimitiveTests(unittest.TestCase):
    def test_canonical_json_and_literal_release_digest(self):
        canonical = _required(promotion, "_canonical_json_file_bytes")
        digest = _required(promotion, "_sha256_bytes")
        payload = {"z": "向量", "a": [2, 1], "flag": False}
        expected = b'{"a":[2,1],"flag":false,"z":"\xe5\x90\x91\xe9\x87\x8f"}\n'
        self.assertEqual(canonical(payload), expected)
        self.assertEqual(digest(expected), "72e33b0ecc6de66e86da9e26702bddd5cc0bd61dcc6cf02d83b9ba8dd1f45935")

    def test_relative_paths_and_sha256sums_are_canonical(self):
        relative = _required(promotion, "_relative_path")
        parse = _required(verification, "_parse_sha256sums")
        sha_a = "a" * 64
        sha_b = "b" * 64
        self.assertEqual(relative("images/sha256/aa/file.png"), "images/sha256/aa/file.png")
        for value in ("", ".", "../x", "/x", "a\\b", "a//b", "a\x00b"):
            with self.subTest(value=value), self.assertRaises(InputFormatError):
                relative(value)
        raw = f"{sha_a}  a.txt\n{sha_b}  z.txt\n".encode()
        self.assertEqual(parse(raw), (("a.txt", sha_a), ("z.txt", sha_b)))
        for invalid in (
            f"{sha_b}  z.txt\n{sha_a}  a.txt\n".encode(),
            f"{sha_a} a.txt\n".encode(),
            f"{sha_a}  SHA256SUMS.txt\n".encode(),
            f"{sha_a}  ../x\n".encode(),
            f"{'A' * 64}  a.txt\n".encode(),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(InputFormatError):
                parse(invalid)

    def test_literal_promotion_identity_digest(self):
        identity = _required(promotion, "_promotion_identity")
        payload = {
            "schema_version": "task9-v119-promotion-identity-v1",
            "release_version": "V1.19",
            "baseline_database_sha256": "0" * 64,
            "baseline_question_count": 497,
            "candidate_database_sha256": "1" * 64,
            "candidate_manifest_sha256": "2" * 64,
            "batch_id": "BATCH",
            "preflight_sha256": "3" * 64,
            "import_approval_statement": "USER APPROVED IMPORT BATCH BATCH " + "3" * 64 + " V1.19",
            "promoted_question_count": 5,
            "formal_question_count": 502,
            "formal_sqlite_sha256": "4" * 64,
            "formal_sqlite_semantic_sha256": "5" * 64,
            "images": [],
        }
        self.assertEqual(identity(payload), "4d8e752f2d3ac9d5fb1474c35cea5ad6fb52fb4e2a7c3de96a26455781a0689c")

    def test_candidate_image_projection_uses_top_level_relative_path(self):
        copy_images = _required(promotion, "_copy_images")
        project_images = _required(verification, "_project_candidate_images")
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            target = root / "target"
            relative = "images/sha256/ab/" + "ab" * 32 + ".png"
            source = candidate / relative
            source.parent.mkdir(parents=True)
            source.write_bytes(b"image bytes")
            entry = {
                "bindings": [
                    {
                        "image_order": 0,
                        "proposed_question_id": "Q1",
                        "role": "question",
                        "source_relative_path": "images/source.png",
                    }
                ],
                "kind": "image",
                "relative_path": relative,
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "size_bytes": source.stat().st_size,
            }
            expected = [
                {
                    "relative_path": relative,
                    "sha256": entry["sha256"],
                    "size_bytes": entry["size_bytes"],
                    "kind": "image",
                }
            ]
            self.assertEqual(copy_images(candidate, target, {"images": [entry]}), expected)
            self.assertEqual(project_images({"images": [entry]}), expected)
            self.assertEqual((target / relative).read_bytes(), b"image bytes")


class PromotionSemanticDigestOracleTests(unittest.TestCase):
    def test_literal_semantic_payload_and_digest(self):
        payload_for = _required(promotion, "_sqlite_semantic_payload")
        digest_for = _required(promotion, "_sqlite_semantic_sha256")
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.sqlite3"
            with sqlite3.connect(path) as database:
                database.execute("PRAGMA user_version=119")
                database.execute("CREATE TABLE alpha (id INTEGER PRIMARY KEY, name TEXT, payload BLOB)")
                database.execute(
                    "CREATE VIEW formal_complete_questions_v119 AS "
                    "SELECT id AS formal_order, name, payload FROM alpha ORDER BY id"
                )
                database.execute("INSERT INTO alpha VALUES (2,?,?)", ("β", bytes.fromhex("00ff")))
                database.execute("INSERT INTO alpha VALUES (1,?,NULL)", ("a",))
            expected = {
                "schema_version": "task9-v119-sqlite-semantic-v1",
                "user_version": 119,
                "schema_objects": [
                    {"type": "table", "name": "alpha", "table_name": "alpha", "sql": "CREATE TABLE alpha (id INTEGER PRIMARY KEY, name TEXT, payload BLOB)"},
                    {"type": "view", "name": "formal_complete_questions_v119", "table_name": "formal_complete_questions_v119", "sql": "CREATE VIEW formal_complete_questions_v119 AS SELECT id AS formal_order, name, payload FROM alpha ORDER BY id"},
                ],
                "relations": [
                    {"name": "alpha", "columns": ["id", "name", "payload"], "rows": [[1, "a", None], [2, "β", {"blob_hex": "00ff"}]]},
                    {"name": "formal_complete_questions_v119", "columns": ["formal_order", "name", "payload"], "rows": [[1, "a", None], [2, "β", {"blob_hex": "00ff"}]]},
                ],
            }
            self.assertEqual(payload_for(path, "formal_complete_questions_v119"), expected)
            self.assertEqual(digest_for(path, "formal_complete_questions_v119"), "0b6459a3ce1aa9342b7ed09b130bc9204b2518658065c4f00c9c15d16241cd63")

    def test_semantic_digest_is_physical_path_independent(self):
        digest_for = _required(promotion, "_sqlite_semantic_sha256")
        with TemporaryDirectory() as temporary:
            digests = []
            for name in ("a.sqlite3", "nested/b.sqlite3"):
                path = Path(temporary) / name
                path.parent.mkdir(exist_ok=True)
                with sqlite3.connect(path) as database:
                    database.execute("PRAGMA user_version=119")
                    database.execute("CREATE TABLE t(k TEXT PRIMARY KEY, value INTEGER)")
                    database.execute("INSERT INTO t VALUES ('x', 1)")
                    database.execute("CREATE VIEW formal_complete_questions_v119 AS SELECT rowid AS formal_order,* FROM t ORDER BY formal_order")
                digests.append(digest_for(path, "formal_complete_questions_v119"))
            self.assertEqual(digests[0], digests[1])


if __name__ == "__main__":
    unittest.main()
