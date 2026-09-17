"""Literal primitive authority for Task 10C promotion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import joy_m2.ingest.v120_promotion as promotion
import joy_m2.ingest.v120_promotion_verification as verification


CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "candidate_binding", "manifest_contract", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v119_preservation", "batch_ledger_closure",
    "promotion_projection", "formal_query", "count_closure",
    "provenance_closure", "deterministic_identity", "publication_boundary",
)


class V120PromotionPrimitiveTests(unittest.TestCase):
    def test_exact_check_inventory_is_independently_closed(self) -> None:
        self.assertEqual(getattr(verification, "CHECK_NAMES", None), CHECK_NAMES)

    def test_exact_ddl_and_view_contract_are_present(self) -> None:
        promotion_sql = getattr(promotion, "PROMOTION_TABLE_SQL", "")
        promoted_sql = getattr(promotion, "PROMOTED_TABLE_SQL", "")
        view_sql = getattr(promotion, "FORMAL_VIEW_SQL", "")
        self.assertIn("CREATE TABLE task10_v120_promotion_v1", promotion_sql)
        self.assertIn("accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=3)", promotion_sql)
        self.assertIn("formal_question_count INTEGER NOT NULL CHECK(formal_question_count=543)", promotion_sql)
        self.assertIn("CREATE TABLE task10_v120_promoted_questions_v1", promoted_sql)
        self.assertIn("record_status TEXT NOT NULL CHECK(record_status='published')", promoted_sql)
        self.assertIn("selectable INTEGER NOT NULL CHECK(selectable=1)", promoted_sql)
        self.assertIn("CREATE VIEW formal_complete_questions_v120", view_sql)
        self.assertIn("'task10_v120_promoted' AS authority_kind", view_sql)
        expected = {
            "PROMOTION_TABLE_SQL": "2115665bedf2fc1f113f7115f08ff87e2080a43bd212a0b85dd5280f271198f3",
            "PROMOTED_TABLE_SQL": "faac12a21ef0376cbecdb021ecf983d512394d5254780b4ba0311454aefda9a2",
            "FORMAL_VIEW_SQL": "8aeea01bf1b8cef79cbd4f508b80559abe5a676c678a83f310921985f719df93",
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                verifier_sql = getattr(verification, f"_{name}", None)
                self.assertIsInstance(verifier_sql, str)
                normalized = promotion._normalize_sql(verifier_sql).encode("utf-8")
                self.assertEqual(hashlib.sha256(normalized).hexdigest(), digest)
                self.assertEqual(
                    promotion._normalize_sql(getattr(promotion, name)),
                    promotion._normalize_sql(verifier_sql),
                )

    def test_canonical_json_and_promotion_identity_literal_oracle(self) -> None:
        canonical = getattr(promotion, "_canonical_json_file_bytes", None)
        self.assertTrue(callable(canonical))
        payload = {"z": [3, 2, 1], "a": {"β": "值", "n": 543}}
        expected = '{"a":{"n":543,"β":"值"},"z":[3,2,1]}\n'.encode()
        self.assertEqual(canonical(payload), expected)
        identity = getattr(promotion, "_promotion_identity", None)
        self.assertTrue(callable(identity))
        self.assertEqual(identity(payload), hashlib.sha256(expected).hexdigest())

    def test_sqlite_semantic_payload_is_path_independent(self) -> None:
        semantic = getattr(promotion, "_sqlite_semantic_payload", None)
        self.assertTrue(callable(semantic))
        with tempfile.TemporaryDirectory() as directory:
            roots = [Path(directory) / "a.sqlite3", Path(directory) / "deep/b.sqlite3"]
            roots[1].parent.mkdir()
            for path in roots:
                with sqlite3.connect(path) as database:
                    database.execute("CREATE TABLE example (id INTEGER PRIMARY KEY, value TEXT)")
                    database.execute("INSERT INTO example VALUES (1,'x')")
                    database.execute("CREATE VIEW formal_complete_questions_v120 AS SELECT id AS formal_order,value FROM example")
                    database.execute("PRAGMA user_version=120")
            first = semantic(roots[0], "formal_complete_questions_v120")
            second = semantic(roots[1], "formal_complete_questions_v120")
        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "task10-v120-sqlite-semantic-v1")
        self.assertEqual(first["user_version"], 120)

    def test_exact_candidate_binding_constants(self) -> None:
        expected = {
            "CANDIDATE_DIGEST": "88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3",
            "CANDIDATE_SHA256": "d8ff5bf9e38f27e23e72c39ae41cb297b4223fde5d2bc149178a7033fe9769d1",
            "CANDIDATE_MANIFEST_SHA256": "673a598b7d5b59394ebaf1307943f90a293c165ecc7aa349c23c2947397f5052",
            "BASELINE_SHA256": "5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff",
            "BASELINE_RELEASE_DIGEST": "7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d",
        }
        for name, value in expected.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(promotion, name, None), value)
                self.assertEqual(getattr(verification, name, None), value)


if __name__ == "__main__":
    unittest.main()
