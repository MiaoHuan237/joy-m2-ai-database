"""Literal behavior authority for V1.22 formal promotion readiness."""

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

import joy_m2.ingest.v122_promotion as promotion
import joy_m2.ingest.v122_promotion_verification as verification


CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "candidate_binding", "manifest_contract", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v121_preservation", "batch_ledger_closure",
    "promotion_projection", "formal_query", "count_closure",
    "provenance_closure", "deterministic_identity", "publication_boundary",
)

CONSTANTS = {
    "CANDIDATE_DIGEST": "82b10a551f70eebda2e0aa4d10c962e317767e936b4f0d9aa798629bb8070d46",
    "CANDIDATE_SHA256": "f1adf0ff7c2034445b1ee4724c03e8c66c6026c5e94d37cc469e1b350c2a9a7a",
    "CANDIDATE_MANIFEST_SHA256": "dc974a1f3180fc3d7d416385242d21aec78266f4e52f5a9de5732f31d57a5403",
    "BASELINE_SHA256": "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a",
    "BASELINE_RELEASE_DIGEST": "f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3",
}


class V122PromotionPrimitiveTests(unittest.TestCase):
    def test_exact_check_inventory_is_independently_closed(self) -> None:
        self.assertEqual(getattr(verification, "CHECK_NAMES", None), CHECK_NAMES)

    def test_exact_candidate_and_baseline_constants(self) -> None:
        for name, value in CONSTANTS.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(promotion, name, None), value)
                self.assertEqual(getattr(verification, name, None), value)
        for name, value in (
            ("CANDIDATE_SIZE", 10_330_112),
            ("CANDIDATE_MANIFEST_SIZE", 6_851),
            ("BASELINE_SIZE", 10_063_872),
            ("BASELINE_MANIFEST_SHA256", "a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40"),
            ("BASELINE_MANIFEST_SIZE", 7_913),
        ):
            with self.subTest(name=name):
                self.assertEqual(getattr(promotion, name, None), value)
                self.assertEqual(getattr(verification, name, None), value)

    def test_exact_ddl_and_formal_view_contract(self) -> None:
        promotion_sql = getattr(promotion, "PROMOTION_TABLE_SQL", "")
        promoted_sql = getattr(promotion, "PROMOTED_TABLE_SQL", "")
        view_sql = getattr(promotion, "FORMAL_VIEW_SQL", "")
        self.assertIn("CREATE TABLE task12_v122_promotion_v1", promotion_sql)
        self.assertIn("accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=4)", promotion_sql)
        self.assertIn("formal_question_count INTEGER NOT NULL CHECK(formal_question_count=639)", promotion_sql)
        self.assertIn("CREATE TABLE task12_v122_promoted_questions_v1", promoted_sql)
        self.assertIn("batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 4)", promoted_sql)
        self.assertIn("formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 592 AND 639)", promoted_sql)
        self.assertIn("record_status TEXT NOT NULL CHECK(record_status='published')", promoted_sql)
        self.assertIn("selectable INTEGER NOT NULL CHECK(selectable=1)", promoted_sql)
        self.assertIn("CREATE VIEW formal_complete_questions_v122", view_sql)
        self.assertIn("SELECT * FROM formal_complete_questions_v121", view_sql)
        self.assertIn("'task12_v122_promoted' AS authority_kind", view_sql)
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
        payload = {"z": [4, 3, 2, 1], "a": {"β": "值", "n": 639}}
        expected = '{"a":{"n":639,"β":"值"},"z":[4,3,2,1]}\n'.encode()
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
                    database.execute("CREATE VIEW formal_complete_questions_v122 AS SELECT id AS formal_order,value FROM example")
                    database.execute("PRAGMA user_version=122")
            first = semantic(paths[0], "formal_complete_questions_v122")
            second = semantic(paths[1], "formal_complete_questions_v122")
        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "task12-v122-sqlite-semantic-v1")
        self.assertEqual(first["user_version"], 122)


if __name__ == "__main__":
    unittest.main()
