"""Literal behavior authority for V1.21 formal promotion readiness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import joy_m2.ingest.v121_promotion as promotion
import joy_m2.ingest.v121_promotion_verification as verification


CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "candidate_binding", "manifest_contract", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v120_preservation", "batch_ledger_closure",
    "promotion_projection", "formal_query", "count_closure",
    "provenance_closure", "deterministic_identity", "publication_boundary",
)

CONSTANTS = {
    "CANDIDATE_DIGEST": "ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c",
    "CANDIDATE_SHA256": "6e27e5b5eff5a701b4671a3e12ee538eed985147d86c23edef1e9489f714a53c",
    "CANDIDATE_MANIFEST_SHA256": "dc82e04639a4b54e24bbf7eceeb4ecec8a3751dfa7e8595f260b9d894d91fc83",
    "BASELINE_SHA256": "b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292",
    "BASELINE_RELEASE_DIGEST": "1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf",
}


class V121PromotionPrimitiveTests(unittest.TestCase):
    def test_exact_check_inventory_is_independently_closed(self) -> None:
        self.assertEqual(getattr(verification, "CHECK_NAMES", None), CHECK_NAMES)

    def test_exact_candidate_and_baseline_constants(self) -> None:
        for name, value in CONSTANTS.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(promotion, name, None), value)
                self.assertEqual(getattr(verification, name, None), value)
        for name, value in (
            ("CANDIDATE_SIZE", 9_957_376),
            ("CANDIDATE_MANIFEST_SIZE", 6_849),
            ("BASELINE_SIZE", 9_768_960),
            ("BASELINE_MANIFEST_SHA256", "19ac2e43ded74a3f3eaf75c184b5eb231c9f1b0b152f5914cd822a321b045098"),
            ("BASELINE_MANIFEST_SIZE", 6_643),
        ):
            with self.subTest(name=name):
                self.assertEqual(getattr(promotion, name, None), value)
                self.assertEqual(getattr(verification, name, None), value)

    def test_exact_ddl_and_formal_view_contract(self) -> None:
        promotion_sql = getattr(promotion, "PROMOTION_TABLE_SQL", "")
        promoted_sql = getattr(promotion, "PROMOTED_TABLE_SQL", "")
        view_sql = getattr(promotion, "FORMAL_VIEW_SQL", "")
        self.assertIn("CREATE TABLE task11_v121_promotion_v1", promotion_sql)
        self.assertIn("accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=4)", promotion_sql)
        self.assertIn("formal_question_count INTEGER NOT NULL CHECK(formal_question_count=591)", promotion_sql)
        self.assertIn("CREATE TABLE task11_v121_promoted_questions_v1", promoted_sql)
        self.assertIn("batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 4)", promoted_sql)
        self.assertIn("formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 544 AND 591)", promoted_sql)
        self.assertIn("record_status TEXT NOT NULL CHECK(record_status='published')", promoted_sql)
        self.assertIn("selectable INTEGER NOT NULL CHECK(selectable=1)", promoted_sql)
        self.assertIn("CREATE VIEW formal_complete_questions_v121", view_sql)
        self.assertIn("SELECT * FROM formal_complete_questions_v120", view_sql)
        self.assertIn("'task11_v121_promoted' AS authority_kind", view_sql)
        normalize = getattr(promotion, "_normalize_sql", None)
        self.assertTrue(callable(normalize))
        for name in ("PROMOTION_TABLE_SQL", "PROMOTED_TABLE_SQL", "FORMAL_VIEW_SQL"):
            self.assertEqual(
                normalize(getattr(promotion, name)),
                normalize(getattr(verification, f"_{name}")),
            )

    def test_canonical_json_and_promotion_identity_literal_oracle(self) -> None:
        canonical = getattr(promotion, "_canonical_json_file_bytes", None)
        identity = getattr(promotion, "_promotion_identity", None)
        self.assertTrue(callable(canonical))
        self.assertTrue(callable(identity))
        payload = {"z": [4, 3, 2, 1], "a": {"β": "值", "n": 591}}
        expected = '{"a":{"n":591,"β":"值"},"z":[4,3,2,1]}\n'.encode()
        self.assertEqual(canonical(payload), expected)
        self.assertEqual(identity(payload), hashlib.sha256(expected).hexdigest())

    def test_sqlite_semantic_payload_is_path_independent(self) -> None:
        semantic = getattr(promotion, "_sqlite_semantic_payload", None)
        self.assertTrue(callable(semantic))
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / "a.sqlite3", Path(directory) / "deep/b.sqlite3"]
            paths[1].parent.mkdir()
            for path in paths:
                with sqlite3.connect(path) as database:
                    database.execute("CREATE TABLE example (id INTEGER PRIMARY KEY, value TEXT)")
                    database.execute("INSERT INTO example VALUES (1,'x')")
                    database.execute("CREATE VIEW formal_complete_questions_v121 AS SELECT id AS formal_order,value FROM example")
                    database.execute("PRAGMA user_version=121")
            first = semantic(paths[0], "formal_complete_questions_v121")
            second = semantic(paths[1], "formal_complete_questions_v121")
        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "task11-v121-sqlite-semantic-v1")
        self.assertEqual(first["user_version"], 121)


if __name__ == "__main__":
    unittest.main()
