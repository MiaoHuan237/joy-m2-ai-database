from __future__ import annotations

import collections
import csv
import hashlib
import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from task6_work.build_task6_release import (
    TABLE_COLUMNS,
    audit_candidates,
    build_release,
    build_sqlite,
    extract_legacy_candidates,
    package_release,
    validate_baseline,
)
from task6_work.verify_task6_release import verify_release


ROOT = Path(__file__).resolve().parents[1]
V117_DIR = ROOT / "outputs/25757421d1d8/Task5_V1.17_正式入库"
V117_DB = V117_DIR / "Joy_M2_Complete_Question_DB_V1_17.sqlite3"
V117_MANIFEST = V117_DIR / "manifest.json"
V117_DB_SHA256 = "58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab"
EXCLUDED_SOURCE_ID = "M2QD-DIFFERENTIATION-APPLICATIONS"


class Task6BaselineTests(unittest.TestCase):
    def test_v117_baseline_hash_and_existing_v2_count_are_locked(self) -> None:
        validate_baseline(V117_DB, V117_MANIFEST)
        self.assertEqual(hashlib.sha256(V117_DB.read_bytes()).hexdigest(), V117_DB_SHA256)
        with sqlite3.connect(V117_DB) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone()[0], 45)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complete_questions").fetchone()[0], 497)

    def test_extractor_returns_exactly_452_unique_questions_from_23_sources(self) -> None:
        records = extract_legacy_candidates(V117_DB)
        self.assertEqual(len(records), 452)
        self.assertEqual(len({row["question_id"] for row in records}), 452)
        self.assertEqual(len({row["source_id"] for row in records}), 23)
        self.assertNotIn(EXCLUDED_SOURCE_ID, {row["source_id"] for row in records})
        self.assertTrue(all(row["record_kind"] in {"complete", "both"} for row in records))

    def test_extractor_preserves_stable_source_distribution(self) -> None:
        records = extract_legacy_candidates(V117_DB)
        counts: dict[str, int] = {}
        for row in records:
            counts[row["source_id"]] = counts.get(row["source_id"], 0) + 1
        self.assertEqual(sum(counts.values()), 452)
        self.assertEqual(counts["DSE-2021"], 12)
        self.assertEqual(counts["DSE-2026"], 12)
        self.assertEqual(counts["M2QD-APPLICATIONS-INTEGRATION"], 35)
        self.assertEqual(counts["M2WANG-APPLICATIONS-OF-DIFFERENTIATION"], 42)
        self.assertEqual(counts["M2WANG-VECTORS-APPLICATIONS"], 17)


class Task6AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records, cls.report = audit_candidates(V117_DB, ROOT)
        cls.by_id = {row["question_id"]: row for row in cls.records}

    def test_every_candidate_satisfies_the_complete_question_contract(self) -> None:
        self.assertEqual(len(self.records), 452)
        self.assertEqual(len(self.by_id), 452)
        for row in self.records:
            self.assertEqual(set(row), set(TABLE_COLUMNS))
            self.assertTrue(row["question_text_original"].strip(), row["question_id"])
            self.assertTrue(row["question_text_zh_reviewed"].strip(), row["question_id"])
            self.assertIn(row["difficulty_level"], range(1, 6), row["question_id"])
            self.assertEqual(row["record_status"], "audit_passed", row["question_id"])
            self.assertEqual(row["unresolved_issues"], [], row["question_id"])
            self.assertFalse(row["question_id"].endswith(("-a", "-b", "-i", "-ii")))

    def test_answer_statuses_preserve_real_provenance(self) -> None:
        counts = collections.Counter(row["answer_status"] for row in self.records)
        self.assertEqual(
            counts,
            collections.Counter(
                {"source_provided": 347, "ai_solved_verified": 71, "missing_from_source": 34}
            ),
        )
        for row in self.records:
            if row["answer_status"] == "missing_from_source":
                self.assertEqual(row["solution_verified"], "", row["question_id"])
                self.assertEqual(row["answer_verification_status"], "not_available")
            else:
                self.assertTrue(row["solution_verified"].strip(), row["question_id"])

    def test_source_and_fragment_hashes_are_complete(self) -> None:
        digest = re.compile(r"^[0-9a-f]{64}$")
        for row in self.records:
            self.assertRegex(row["source_sha256"], digest, row["question_id"])
            self.assertRegex(row["source_member_sha256"], digest, row["question_id"])
            self.assertRegex(row["source_fragment_hash"], digest, row["question_id"])
            self.assertRegex(row["solution_source_member_sha256"], digest, row["question_id"])
            self.assertTrue(row["source_member"].strip(), row["question_id"])

    def test_tags_are_clean_single_line_controlled_terms(self) -> None:
        valid = re.compile(r"^[A-Za-z0-9_\-\u4e00-\u9fff、]+$")
        for row in self.records:
            self.assertGreaterEqual(len(row["tags"]), 1, row["question_id"])
            self.assertIn(row["primary_type"], row["tags"], row["question_id"])
            self.assertEqual(len(row["tags"]), len(set(row["tags"])), row["question_id"])
            for tag in row["tags"]:
                self.assertRegex(tag, valid, (row["question_id"], tag))
                self.assertNotIn("检查项目", tag)

    def test_2026_marks_and_difficulty_are_derived_without_claiming_official_answers(self) -> None:
        expected_marks = {
            "2026-Q1": 4, "2026-Q2": 6, "2026-Q3": 6, "2026-Q4": 6,
            "2026-Q5": 6, "2026-Q6": 6, "2026-Q7": 8, "2026-Q8": 8,
            "2026-Q9": 13, "2026-Q10": 12, "2026-Q11": 12, "2026-Q12": 13,
        }
        expected_levels = {
            "2026-Q1": 2, "2026-Q2": 2, "2026-Q3": 2, "2026-Q4": 2,
            "2026-Q5": 3, "2026-Q6": 3, "2026-Q7": 4, "2026-Q8": 4,
            "2026-Q9": 4, "2026-Q10": 4, "2026-Q11": 4, "2026-Q12": 4,
        }
        self.assertEqual(sum(expected_marks.values()), 100)
        for question_id, marks in expected_marks.items():
            row = self.by_id[question_id]
            self.assertEqual(row["marks_total"], marks)
            self.assertEqual(row["difficulty_level"], expected_levels[question_id])
            self.assertEqual(row["answer_status"], "ai_solved_verified")
            self.assertEqual(row["official_marking_available"], False)
        self.assertIn("严谨性", self.by_id["2026-Q8"]["audit_notes"])

    def test_images_exist_and_exact_duplicate_audit_is_clear(self) -> None:
        image_refs = 0
        for row in self.records:
            for relative in row["image_paths"]:
                image_refs += 1
                self.assertTrue((ROOT / relative).is_file(), (row["question_id"], relative))
            self.assertNotEqual(row["duplicate_status"], "exact_duplicate", row["question_id"])
        self.assertEqual(image_refs, 33)
        self.assertEqual(self.report["exact_duplicate_count"], 0)
        self.assertEqual(self.report["audit_passed"], 452)
        self.assertEqual(self.report["audit_pending"], 0)
        self.assertEqual(self.report["blocked"], 0)


def logical_table_digest(db_path: Path, table: str) -> str:
    with sqlite3.connect(db_path) as db:
        columns = [row[1] for row in db.execute(f"PRAGMA table_info({table})")]
        order = ",".join(f'"{column}"' for column in columns)
        rows = db.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Task6SQLiteMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.output_db = Path(cls.tempdir.name) / "Joy_M2_Complete_Question_DB_V1_18.sqlite3"
        records, report = audit_candidates(V117_DB, ROOT)
        build_sqlite(V117_DB, cls.output_db, records, report)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tempdir.cleanup()

    def test_v118_contains_497_published_complete_questions(self) -> None:
        with sqlite3.connect(self.output_db) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 118)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone()[0], 497)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM selectable_complete_questions_v2").fetchone()[0], 497)
            self.assertEqual(
                db.execute("SELECT COUNT(DISTINCT source_order) FROM complete_questions_v2").fetchone()[0],
                497,
            )
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM complete_questions_v2 WHERE record_status<>'published' OR joy_approval<>'approved_by_joy'").fetchone()[0],
                0,
            )

    def test_v117_complete_rows_and_legacy_tables_are_logically_unchanged(self) -> None:
        for table in ["sources", "questions", "topics", "question_topics"]:
            self.assertEqual(
                logical_table_digest(self.output_db, table),
                logical_table_digest(V117_DB, table),
                table,
            )
        with sqlite3.connect(V117_DB) as old_db, sqlite3.connect(self.output_db) as new_db:
            old_rows = old_db.execute("SELECT * FROM complete_questions_v2 ORDER BY question_id").fetchall()
            new_rows = new_db.execute("SELECT * FROM complete_questions_v2 WHERE source_order<=45 ORDER BY question_id").fetchall()
            self.assertEqual(new_rows, old_rows)

    def test_task6_import_run_and_release_metadata_are_complete(self) -> None:
        with sqlite3.connect(self.output_db) as db:
            metadata = dict(db.execute("SELECT key,value FROM release_metadata_v2"))
            self.assertEqual(metadata["release_version"], "V1.18")
            self.assertEqual(metadata["audited_v2_questions"], "497")
            self.assertEqual(metadata["remaining_unmigrated_complete_questions"], "0")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM import_runs_v2").fetchone()[0], 2)
            task6 = db.execute(
                "SELECT release_version,imported_question_count,status FROM import_runs_v2 WHERE import_id LIKE 'TASK6-%'"
            ).fetchone()
            self.assertEqual(task6, ("V1.18", 452, "completed"))

    def test_taxonomy_covers_every_primary_type_and_tag(self) -> None:
        with sqlite3.connect(self.output_db) as db:
            primary = {row[0] for row in db.execute("SELECT DISTINCT primary_type FROM complete_questions_v2")}
            primary_vocab = {
                row[0] for row in db.execute(
                    "SELECT value FROM complete_question_taxonomy_v2 WHERE taxonomy_kind='primary_type'"
                )
            }
            tags = {
                row[0] for row in db.execute("SELECT DISTINCT tag FROM complete_question_tags_v2")
            }
            tag_vocab = {
                row[0] for row in db.execute(
                    "SELECT value FROM complete_question_taxonomy_v2 WHERE taxonomy_kind='tag'"
                )
            }
            self.assertEqual(primary_vocab, primary)
            self.assertEqual(tag_vocab, tags)

    def test_full_answer_status_distribution_remains_truthful(self) -> None:
        with sqlite3.connect(self.output_db) as db:
            counts = dict(
                db.execute("SELECT answer_status,COUNT(*) FROM complete_questions_v2 GROUP BY answer_status")
            )
            self.assertEqual(
                counts,
                {"source_provided": 392, "ai_solved_verified": 71, "missing_from_source": 34},
            )
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complete_question_corrections_v2").fetchone()[0], 59)


class Task6DerivedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.output_dir = Path(cls.tempdir.name) / "Task6_V1.18_正式入库"
        cls.paths = build_release(V117_DIR, cls.output_dir, ROOT)
        cls.db_path = cls.output_dir / "Joy_M2_Complete_Question_DB_V1_18.sqlite3"
        cls.csv_path = cls.output_dir / "Joy_M2_Complete_Questions_V1_18.csv"
        cls.knowledge_path = cls.output_dir / "Joy_M2_完整题497题_知识文档_V1.18.md"
        cls.report_path = cls.output_dir / "Joy_M2_V1.18_正式入库报告.md"
        cls.state_path = cls.output_dir / "PROJECT_STATE.md"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tempdir.cleanup()

    def test_all_requested_artifacts_exist(self) -> None:
        expected = {
            "Joy_M2_Complete_Question_DB_V1_18.sqlite3",
            "Joy_M2_Complete_Questions_V1_18.csv",
            "Joy_M2_完整题497题_知识文档_V1.18.md",
            "Joy_M2_V1.18_正式入库报告.md",
            "PROJECT_STATE.md",
            "complete_questions_452_task6_audited.json",
            "task6_audit_report.json",
        }
        self.assertTrue(expected.issubset({path.name for path in self.output_dir.iterdir()}))

    def test_csv_is_an_exact_497_row_flat_mirror(self) -> None:
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            db_rows = [dict(row) for row in db.execute("SELECT * FROM complete_questions_v2 ORDER BY question_id")]
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            csv_rows = list(reader)
            self.assertEqual(reader.fieldnames, list(db_rows[0]))
        self.assertEqual(len(csv_rows), 497)
        for db_row, csv_row in zip(db_rows, csv_rows, strict=True):
            expected = {key: "" if value is None else str(value) for key, value in db_row.items()}
            self.assertEqual(csv_row, expected, db_row["question_id"])

    def test_markdown_contains_all_questions_and_truthful_answer_states(self) -> None:
        text = self.knowledge_path.read_text(encoding="utf-8")
        headings = re.findall(r"^### \d+\. `([^`]+)`$", text, flags=re.MULTILINE)
        self.assertEqual(len(headings), 497)
        self.assertEqual(len(set(headings)), 497)
        self.assertEqual(text.count("答案状态：`missing_from_source`"), 34)
        self.assertIn("一道完整题一条记录，不拆分小问", text)
        self.assertIn("2026-Q8", text)
        self.assertIn("断开定义域", text)

    def test_report_and_project_state_declare_full_v2_coverage(self) -> None:
        report = self.report_path.read_text(encoding="utf-8")
        state = self.state_path.read_text(encoding="utf-8")
        for token in ["V1.18", "497", "452", "P0=0", "P1=0", "34", "71", "392"]:
            self.assertIn(token, report)
        self.assertIn("原始 Mathpix ZIP", report)
        self.assertIn("当前正式数据版本：Joy DSE M2 题库 V1.18", state)
        self.assertIn("新完整题层：497道", state)
        self.assertIn("剩余未迁移完整题：0道", state)
        self.assertNotIn("当前唯一优先任务：按新标准审计并迁移其余452道完整题", state)

    def test_audit_json_is_complete_and_deterministic(self) -> None:
        records = json.loads(
            (self.output_dir / "complete_questions_452_task6_audited.json").read_text(encoding="utf-8")
        )
        report = json.loads((self.output_dir / "task6_audit_report.json").read_text(encoding="utf-8"))
        self.assertEqual(len(records), 452)
        self.assertEqual(report["audit_passed"], 452)
        self.assertEqual(report["audit_pending"], 0)
        self.assertEqual(report["blocked"], 0)


class Task6PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tempdir.name)
        cls.release_dir = cls.root / "Task6_V1.18_正式入库"
        build_release(V117_DIR, cls.release_dir, ROOT)
        cls.zip_one = cls.root / "release-one.zip"
        cls.zip_two = cls.root / "release-two.zip"
        package_release(cls.release_dir, cls.zip_one)
        package_release(cls.release_dir, cls.zip_two)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tempdir.cleanup()

    def test_package_is_byte_deterministic_and_contains_evidence(self) -> None:
        self.assertEqual(self.zip_one.read_bytes(), self.zip_two.read_bytes())
        import zipfile

        with zipfile.ZipFile(self.zip_one) as archive:
            names = archive.namelist()
        required_suffixes = {
            "Joy_M2_Complete_Question_DB_V1_18.sqlite3",
            "Joy_M2_Complete_Questions_V1_18.csv",
            "Joy_M2_完整题497题_知识文档_V1.18.md",
            "Joy_M2_V1.18_正式入库报告.md",
            "PROJECT_STATE.md",
            "complete_questions_452_task6_audited.json",
            "task6_audit_report.json",
            "task6_verification.json",
            "build_task6_release.py",
            "verify_task6_release.py",
            "test_task6_migration.py",
            "task6_contract.json",
            "manifest.json",
            "SHA256SUMS.txt",
        }
        self.assertTrue(required_suffixes.issubset({Path(name).name for name in names}))
        self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))

    def test_manifest_and_sha256s_cover_every_protected_file(self) -> None:
        manifest = json.loads((self.release_dir / "manifest.json").read_text(encoding="utf-8"))
        for name, expected in manifest["artifact_sha256"].items():
            self.assertEqual(hashlib.sha256((self.release_dir / name).read_bytes()).hexdigest(), expected)
        sums = {}
        for line in (self.release_dir / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            sums[name] = digest
        protected = {
            path.name for path in self.release_dir.iterdir() if path.name != "SHA256SUMS.txt"
        }
        self.assertEqual(set(sums), protected)
        for name, expected in sums.items():
            self.assertEqual(hashlib.sha256((self.release_dir / name).read_bytes()).hexdigest(), expected)

    def test_independent_extracted_package_verifier_passes(self) -> None:
        import zipfile

        extract_root = self.root / "extracted"
        with zipfile.ZipFile(self.zip_one) as archive:
            archive.extractall(extract_root)
        extracted_release = next(path for path in extract_root.iterdir() if path.is_dir())
        result = verify_release(extracted_release)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["question_count"], 497)
        self.assertEqual(result["task6_question_count"], 452)
        self.assertEqual(result["csv_row_count"], 497)
        self.assertEqual(result["markdown_question_count"], 497)


if __name__ == "__main__":
    unittest.main()
