from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE_DIR = ROOT / "releases/V1.18"
LOCK_PATH = ROOT / "data/baselines/V1.18/BASELINE_LOCK.json"

EXPECTED_SUMS_SHA256 = "ae7fea3558a8942262ab8578a66d9d4c3330fe0c9683de9aeaedac462bb750f3"
EXPECTED_SQLITE_SHA256 = "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
EXPECTED_SOURCE_ZIP_SHA256 = "302782a47f347ce2b75a7813903f5d0b4c29fae2e0a837ccdc98b7b3439b4d4e"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ProjectStructureTests(unittest.TestCase):
    def test_required_project_entries_exist(self) -> None:
        required = [
            "AGENTS.md",
            "PROJECT_CONTEXT.md",
            "PROJECT_STATE.md",
            "README.md",
            "pyproject.toml",
            "src/joy_m2",
            "src/joy_m2/audit",
            "src/joy_m2/db",
            "src/joy_m2/export",
            "src/joy_m2/release",
            "tests/unit",
            "tests/integration",
            "data/raw",
            "data/baselines/V1.18",
            "data/staging",
            "releases/V1.18",
            "docs/architecture",
            "docs/decisions",
            "docs/reports",
            "scripts",
        ]
        missing = [relative for relative in required if not (ROOT / relative).exists()]
        self.assertEqual(missing, [])

    def test_task7_does_not_implement_the_task8_pipeline(self) -> None:
        forbidden = [
            ROOT / "src/joy_m2/cli.py",
            ROOT / "src/joy_m2/audit/pipeline.py",
            ROOT / "src/joy_m2/db/migrate.py",
            ROOT / "src/joy_m2/export/pipeline.py",
            ROOT / "src/joy_m2/release/pipeline.py",
        ]
        self.assertEqual([str(path.relative_to(ROOT)) for path in forbidden if path.exists()], [])

    def test_minimal_legacy_regression_snapshot_is_present(self) -> None:
        required = [
            "legacy/task4_work/task3_package/06_构建与测试/test_task3_review.py",
            "legacy/task4_work/task4_package/05_构建与测试/test_task4_decisions.py",
            "legacy/task4_work/task4_package/05_构建与测试/test_task4_workbook.py",
            "legacy/task5_work/build_task5_release.py",
            "legacy/task5_work/test_task5_import.py",
            "legacy/task5_work/v116/m2_question_bank/data/m2_question_bank.sqlite3",
            "legacy/task6_work/build_task6_release.py",
            "legacy/task6_work/test_task6_migration.py",
            "legacy/task6_work/verify_task6_release.py",
            "legacy/outputs/25757421d1d8/Task5_V1.17_正式入库/manifest.json",
        ]
        missing = [relative for relative in required if not (ROOT / relative).is_file()]
        self.assertEqual(missing, [])


class FrozenV118BaselineTests(unittest.TestCase):
    def test_baseline_lock_contains_the_approved_immutable_values(self) -> None:
        self.assertTrue(LOCK_PATH.is_file(), str(LOCK_PATH.relative_to(ROOT)))
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(lock["release_version"], "V1.18")
        self.assertEqual(lock["question_counts"], {"all": 497, "task6": 452, "v117": 45})
        self.assertEqual(
            lock["answer_status_counts"],
            {"source_provided": 392, "ai_solved_verified": 71, "missing_from_source": 34},
        )
        self.assertEqual(lock["sha256sums_sha256"], EXPECTED_SUMS_SHA256)
        self.assertEqual(lock["sqlite_sha256"], EXPECTED_SQLITE_SHA256)
        self.assertEqual(lock["source_release_zip_sha256"], EXPECTED_SOURCE_ZIP_SHA256)

    def test_release_hashes_match_the_frozen_lock(self) -> None:
        self.assertTrue((RELEASE_DIR / "SHA256SUMS.txt").is_file())
        self.assertTrue((RELEASE_DIR / "Joy_M2_Complete_Question_DB_V1_18.sqlite3").is_file())
        self.assertEqual(sha256(RELEASE_DIR / "SHA256SUMS.txt"), EXPECTED_SUMS_SHA256)
        self.assertEqual(
            sha256(RELEASE_DIR / "Joy_M2_Complete_Question_DB_V1_18.sqlite3"),
            EXPECTED_SQLITE_SHA256,
        )

    def test_embedded_release_verifier_passes(self) -> None:
        verifier_path = RELEASE_DIR / "verify_task6_release.py"
        self.assertTrue(verifier_path.is_file())
        spec = importlib.util.spec_from_file_location("task7_v118_verifier", verifier_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.verify_release(RELEASE_DIR)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["question_count"], 497)
        self.assertEqual(result["task6_question_count"], 452)
        self.assertEqual(result["existing_v117_question_count"], 45)
        self.assertEqual(result["csv_row_count"], 497)
        self.assertEqual(result["markdown_question_count"], 497)

    def test_sqlite_integrity_and_answer_identity_are_unchanged(self) -> None:
        db_path = RELEASE_DIR / "Joy_M2_Complete_Question_DB_V1_18.sqlite3"
        self.assertTrue(db_path.is_file())
        with sqlite3.connect(db_path) as db:
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(
                dict(
                    db.execute(
                        "SELECT answer_status, COUNT(*) "
                        "FROM complete_questions_v2 GROUP BY answer_status"
                    )
                ),
                {"source_provided": 392, "ai_solved_verified": 71, "missing_from_source": 34},
            )
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone()[0],
                497,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
