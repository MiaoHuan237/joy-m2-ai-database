"""Literal behavior authority for V1.24 formal promotion readiness."""

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

import joy_m2.ingest.v124_promotion as promotion
import joy_m2.ingest.v124_promotion_verification as verification


CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "candidate_binding", "manifest_contract", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v123_preservation", "batch_ledger_closure",
    "promotion_projection", "formal_query", "count_closure",
    "provenance_closure", "deterministic_identity", "publication_boundary", "image_projection",
)

CONSTANTS = {
    "CANDIDATE_DIGEST": "3f14589da452207d0088cd44689aded7ffbadea0768a85d808a67ae526a5f3ab",
    "CANDIDATE_SHA256": "93acb2b4c333c4cb881c327389569898ab110ab2f436f00f1d40586e0ed4f8a0",
    "CANDIDATE_MANIFEST_SHA256": "34cd37e27370a72e332d7047d9699d3910d853e1276132ce33ec26df4786de94",
    "BASELINE_SHA256": "28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd",
    "BASELINE_RELEASE_DIGEST": "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc",
}


class V124PromotionPrimitiveTests(unittest.TestCase):
    def test_exact_check_inventory_is_independently_closed(self) -> None:
        self.assertEqual(getattr(verification, "CHECK_NAMES", None), CHECK_NAMES)

    def test_exact_candidate_and_baseline_constants(self) -> None:
        for name, value in CONSTANTS.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(promotion, name, None), value)
                self.assertEqual(getattr(verification, name, None), value)
        for name, value in (
            ("CANDIDATE_SIZE", 11_378_688),
            ("CANDIDATE_MANIFEST_SIZE", 676_520),
            ("BASELINE_SIZE", 10_928_128),
            ("BASELINE_MANIFEST_SHA256", "54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498"),
            ("BASELINE_MANIFEST_SIZE", 6_728),
        ):
            with self.subTest(name=name):
                self.assertEqual(getattr(promotion, name, None), value)
                self.assertEqual(getattr(verification, name, None), value)

    def test_exact_ddl_and_formal_view_contract(self) -> None:
        promotion_sql = getattr(promotion, "PROMOTION_TABLE_SQL", "")
        promoted_sql = getattr(promotion, "PROMOTED_TABLE_SQL", "")
        view_sql = getattr(promotion, "FORMAL_VIEW_SQL", "")
        self.assertIn("CREATE TABLE task14_v124_promotion_v1", promotion_sql)
        self.assertIn("accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=8)", promotion_sql)
        self.assertIn("formal_question_count INTEGER NOT NULL CHECK(formal_question_count=791)", promotion_sql)
        self.assertIn("CREATE TABLE task14_v124_promoted_questions_v1", promoted_sql)
        self.assertIn("batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 8)", promoted_sql)
        self.assertIn("formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 678 AND 791)", promoted_sql)
        self.assertIn("record_status TEXT NOT NULL CHECK(record_status='published')", promoted_sql)
        self.assertIn("selectable INTEGER NOT NULL CHECK(selectable=1)", promoted_sql)
        self.assertIn("CREATE VIEW formal_complete_questions_v124", view_sql)
        self.assertIn("SELECT * FROM formal_complete_questions_v123", view_sql)
        self.assertIn("'task14_v124_promoted' AS authority_kind", view_sql)
        normalize = getattr(promotion, "_normalize_sql", None)
        self.assertTrue(callable(normalize))
        for name in ("PROMOTION_TABLE_SQL", "PROMOTED_TABLE_SQL", "FORMAL_VIEW_SQL"):
            self.assertEqual(
                normalize(getattr(promotion, name)),
                normalize(getattr(verification, f"_{name}")),
            )

    def test_baseline_schema_literal_oracle(self):
        candidate = {"baseline": {"database": {"sha256": "a"*64, "size_bytes": 1},
                       "manifest": {"sha256": "b"*64, "size_bytes": 1}}}
        for module in (promotion, verification):
            project = getattr(module, "_baseline_projection", None)
            self.assertTrue(callable(project))
            value = project(candidate)
            self.assertEqual(value["database_schema"], "task13-v123-formal-v1")
            self.assertNotEqual(value["database_schema"], "task11-v121-formal-v1")
            self.assertNotEqual(value["database_schema"], "task14-v124-formal-v1")

    def test_canonical_json_and_promotion_identity_literal_oracle(self) -> None:
        canonical = getattr(promotion, "_canonical_json_file_bytes", None)
        identity = getattr(promotion, "_promotion_identity", None)
        self.assertTrue(callable(canonical))
        self.assertTrue(callable(identity))
        payload = {"z": [4, 3, 2, 1], "a": {"β": "值", "n": 791}}
        expected = '{"a":{"n":791,"β":"值"},"z":[4,3,2,1]}\n'.encode()
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
                    database.execute("CREATE VIEW formal_complete_questions_v124 AS SELECT id AS formal_order,value FROM example")
                    database.execute("PRAGMA user_version=124")
            first = semantic(paths[0], "formal_complete_questions_v124")
            second = semantic(paths[1], "formal_complete_questions_v124")
        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "task14-v124-sqlite-semantic-v1")
        self.assertEqual(first["user_version"], 124)


if __name__ == "__main__":
    unittest.main()
