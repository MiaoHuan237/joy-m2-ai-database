from __future__ import annotations

import contextlib
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "legacy"
FIXTURES = ROOT / "tests" / "fixtures" / "pipeline"
FORMAL_V118 = ROOT / "releases" / "V1.18"
V117_RELEASE = LEGACY / "outputs" / "25757421d1d8" / "Task5_V1.17_正式入库"
PYTHON = Path(sys.executable).resolve()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_fixture(version: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{version}.json").read_text(encoding="utf-8"))


@contextlib.contextmanager
def legacy_import_path(path: Path):
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path.remove(str(path))


class Task5LegacyBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_fixture("V1.17")
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tempdir.name)
        with legacy_import_path(LEGACY / "task5_work"):
            cls.legacy = importlib.import_module("build_task5_release")

        cls.first_output = cls.root / "first" / "release"
        cls.first_output.mkdir(parents=True)
        cls.sentinel = cls.first_output / "sentinel.txt"
        cls.sentinel.write_text("legacy-only", encoding="utf-8")
        cls.first_paths = cls.legacy.build_release(cls.first_output)
        cls.second_paths = cls.legacy.build_release(cls.root / "second" / "release")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tempdir.cleanup()

    def test_build_is_deterministic_and_matches_reviewed_core_hashes(self) -> None:
        self.assertEqual(set(self.first_paths), set(self.second_paths))
        for key in self.first_paths:
            self.assertEqual(
                self.first_paths[key].read_bytes(),
                self.second_paths[key].read_bytes(),
                key,
            )
        self.assertEqual(sha256(self.first_paths["sqlite"]), self.fixture["sqlite_sha256"])
        self.assertEqual(sha256(self.first_paths["csv"]), self.fixture["csv_sha256"])

    def test_build_recursively_clears_an_existing_target(self) -> None:
        self.assertFalse(self.sentinel.exists())

    def test_database_side_effects_match_the_reviewed_contract(self) -> None:
        with sqlite3.connect(self.first_paths["sqlite"]) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 117)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone()[0],
                self.fixture["question_count"],
            )
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM complete_questions").fetchone()[0],
                self.fixture["legacy_complete_question_count"],
            )
            counts = dict(
                db.execute(
                    "SELECT answer_status, COUNT(*) FROM complete_questions_v2 GROUP BY answer_status"
                )
            )
        self.assertEqual(counts, self.fixture["answer_status_counts"])

    def test_rejects_an_unapproved_record_with_value_error(self) -> None:
        records = json.loads(self.legacy.TASK4_JSON.read_text(encoding="utf-8"))
        records[0]["record_status"] = "audit_pending"
        with self.assertRaisesRegex(ValueError, "Unapproved Task 4 record"):
            self.legacy.approve_records(records)


class Task6LegacyBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_fixture("V1.18")
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tempdir.name)
        cls.output = cls.root / "Task6_V1.18_正式入库"
        cls.output.mkdir(parents=True)
        cls.sentinel = cls.output / "sentinel.txt"
        cls.sentinel.write_text("legacy-stale-file", encoding="utf-8")
        with legacy_import_path(LEGACY):
            cls.builder = importlib.import_module("task6_work.build_task6_release")
            cls.verifier = importlib.import_module("task6_work.verify_task6_release")
            cls.paths = cls.builder.build_release(V117_RELEASE, cls.output, LEGACY)
            cls.zip_one = cls.root / "release-one.zip"
            cls.zip_two = cls.root / "release-two.zip"
            cls.builder.package_release(cls.output, cls.zip_one)
            cls.builder.package_release(cls.output, cls.zip_two)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tempdir.cleanup()

    def test_build_matches_all_seven_frozen_primary_artifacts(self) -> None:
        expected_names = {
            "Joy_M2_Complete_Question_DB_V1_18.sqlite3",
            "Joy_M2_Complete_Questions_V1_18.csv",
            "Joy_M2_完整题497题_知识文档_V1.18.md",
            "Joy_M2_V1.18_正式入库报告.md",
            "PROJECT_STATE.md",
            "complete_questions_452_task6_audited.json",
            "task6_audit_report.json",
        }
        self.assertEqual({path.name for path in self.paths.values()}, expected_names)
        for name in expected_names:
            self.assertEqual((self.output / name).read_bytes(), (FORMAL_V118 / name).read_bytes(), name)
        self.assertEqual(sha256(self.paths["db"]), self.fixture["sqlite_sha256"])
        self.assertEqual(sha256(self.paths["csv"]), self.fixture["csv_sha256"])

    def test_build_keeps_stale_files_and_packaging_protects_them(self) -> None:
        self.assertEqual(self.sentinel.read_text(encoding="utf-8"), "legacy-stale-file")
        sums = (self.output / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        self.assertIn(f"{sha256(self.sentinel)}  sentinel.txt", sums)
        with zipfile.ZipFile(self.zip_one) as archive:
            self.assertIn(f"{self.output.name}/sentinel.txt", archive.namelist())

    def test_package_is_deterministic_with_fixed_sorted_metadata(self) -> None:
        self.assertEqual(self.zip_one.read_bytes(), self.zip_two.read_bytes())
        with zipfile.ZipFile(self.zip_one) as archive:
            infos = archive.infolist()
        self.assertEqual([info.filename for info in infos], sorted(info.filename for info in infos))
        self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in infos))
        self.assertTrue(all(info.create_system == 3 for info in infos))
        self.assertTrue(all((info.external_attr >> 16) & 0o777 == 0o644 for info in infos))
        self.assertTrue(all(info.compress_type == zipfile.ZIP_DEFLATED for info in infos))

    def test_extracted_package_passes_the_independent_verifier(self) -> None:
        extract_root = self.root / "extracted"
        with zipfile.ZipFile(self.zip_one) as archive:
            archive.extractall(extract_root)
        extracted_release = extract_root / self.output.name
        result = self.verifier.verify_release(extracted_release)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["question_count"], self.fixture["question_count"])
        self.assertEqual(result["task6_question_count"], self.fixture["task6_question_count"])
        self.assertEqual(
            result["existing_v117_question_count"],
            self.fixture["existing_v117_question_count"],
        )

    def test_verifier_cli_exit_codes_are_zero_one_and_two(self) -> None:
        verifier = ROOT / "releases" / "V1.18" / "verify_task6_release.py"
        passed = subprocess.run(
            [str(PYTHON), str(verifier), str(FORMAL_V118)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertEqual(json.loads(passed.stdout)["status"], "PASS")

        failed_release = self.root / "structured-fail"
        shutil.copytree(self.output, failed_release)
        csv_path = failed_release / self.fixture["csv_name"]
        csv_path.write_bytes(csv_path.read_bytes() + b"\r\n")
        failed = subprocess.run(
            [str(PYTHON), str(verifier), str(failed_release)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(failed.returncode, 1, failed.stderr)
        self.assertEqual(json.loads(failed.stdout)["status"], "FAIL")

        usage = subprocess.run(
            [str(PYTHON), str(verifier)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(usage.returncode, 2)
        self.assertIn("Usage:", usage.stderr)

    def test_verifier_propagates_missing_and_malformed_manifest_exceptions(self) -> None:
        missing = self.root / "missing-manifest"
        missing.mkdir()
        with self.assertRaises(FileNotFoundError):
            self.verifier.verify_release(missing)

        malformed = self.root / "malformed-manifest"
        malformed.mkdir()
        (malformed / "manifest.json").write_text("{", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            self.verifier.verify_release(malformed)

    def test_baseline_hash_failure_precedes_output_creation(self) -> None:
        bad_baseline = self.root / "bad-v117"
        bad_baseline.mkdir()
        (bad_baseline / self.fixture["sqlite_name"].replace("18", "17")).write_bytes(b"not sqlite")
        output = self.root / "must-not-exist"
        with self.assertRaisesRegex(ValueError, "V1.17 SQLite hash mismatch"):
            self.builder.build_release(bad_baseline, output, LEGACY)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
