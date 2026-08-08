import csv
import hashlib
import json
import sqlite3
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DB = ROOT / "task5_work/v116/m2_question_bank/data/m2_question_bank.sqlite3"
TASK4_JSON = ROOT / "task4_work/task4_package/03_候选数据/complete_questions_45_task4.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Task5FormalImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from build_task5_release import build_release

        cls.temp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.temp.name) / "release"
        cls.paths = build_release(cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all_requested_artifacts_exist(self):
        expected = {"sqlite", "csv", "knowledge", "report", "project_state", "manifest", "approved_json", "taxonomy"}
        self.assertTrue(expected.issubset(self.paths))
        for key in expected:
            self.assertTrue(self.paths[key].is_file(), key)
            self.assertGreater(self.paths[key].stat().st_size, 0, key)

    def test_legacy_v116_tables_are_logically_unchanged(self):
        with sqlite3.connect(BASE_DB) as old, sqlite3.connect(self.paths["sqlite"]) as new:
            self.assertEqual(new.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(new.execute("PRAGMA foreign_key_check").fetchall(), [])
            for table, order in [
                ("sources", "source_id"),
                ("topics", "topic_id"),
                ("questions", "question_id"),
                ("question_topics", "question_id, topic_id"),
            ]:
                self.assertEqual(
                    old.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall(),
                    new.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall(),
                    table,
                )
            self.assertEqual(new.execute("SELECT COUNT(*) FROM questions").fetchone()[0], 1517)
            self.assertEqual(new.execute("SELECT COUNT(*) FROM complete_questions").fetchone()[0], 497)
            self.assertEqual(new.execute("SELECT COUNT(*) FROM sources").fetchone()[0], 24)

    def test_v2_contains_only_45_approved_complete_questions(self):
        task4 = json.loads(TASK4_JSON.read_text(encoding="utf-8"))
        expected_ids = {q["question_id"] for q in task4}
        with sqlite3.connect(self.paths["sqlite"]) as db:
            rows = db.execute(
                "SELECT question_id, record_status, joy_approval, approved_at, schema_version, selectable "
                "FROM complete_questions_v2 ORDER BY question_id"
            ).fetchall()
            self.assertEqual({row[0] for row in rows}, expected_ids)
            self.assertEqual(len(rows), 45)
            self.assertTrue(all(row[1] == "published" for row in rows))
            self.assertTrue(all(row[2] == "approved_by_joy" for row in rows))
            self.assertTrue(all(row[3] == "2026-08-08T20:00:00+08:00" for row in rows))
            self.assertTrue(all(row[4] == "complete-question-v1.0" for row in rows))
            self.assertTrue(all(row[5] == 1 for row in rows))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM selectable_complete_questions_v2").fetchone()[0], 45)

    def test_distributions_tags_and_corrections_match_task4(self):
        with sqlite3.connect(self.paths["sqlite"]) as db:
            self.assertEqual(
                dict(db.execute("SELECT difficulty_level, COUNT(*) FROM complete_questions_v2 GROUP BY difficulty_level")),
                {2: 8, 3: 17, 4: 16, 5: 4},
            )
            self.assertEqual(
                dict(db.execute("SELECT primary_type, COUNT(*) FROM complete_questions_v2 GROUP BY primary_type")),
                {"切线与法线": 6, "极值与曲线性质": 24, "最值与最优化": 5, "变率": 5, "综合微分应用": 5},
            )
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complete_question_corrections_v2").fetchone()[0], 59)
            tags = {row[0] for row in db.execute("SELECT DISTINCT tag FROM complete_question_tags_v2")}
            self.assertTrue({"全局最小值", "从基本原理求导", "导数为正区间"}.issubset(tags))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM complete_questions_v2 WHERE unresolved_issues_json != '[]'").fetchone()[0], 0)

    def test_csv_is_exact_flat_mirror_of_v2_table(self):
        with sqlite3.connect(self.paths["sqlite"]) as db:
            db.row_factory = sqlite3.Row
            db_rows = [dict(row) for row in db.execute("SELECT * FROM complete_questions_v2 ORDER BY question_id")]
        with self.paths["csv"].open(encoding="utf-8-sig", newline="") as handle:
            csv_rows = list(csv.DictReader(handle))
        self.assertEqual(len(csv_rows), 45)
        self.assertEqual([row["question_id"] for row in csv_rows], [row["question_id"] for row in db_rows])
        for csv_row, db_row in zip(csv_rows, db_rows):
            for key, value in db_row.items():
                expected = "" if value is None else str(value)
                self.assertEqual(csv_row[key], expected, f"{csv_row['question_id']}:{key}")

    def test_markdown_is_derived_complete_knowledge_document(self):
        text = self.paths["knowledge"].read_text(encoding="utf-8")
        task4 = json.loads(TASK4_JSON.read_text(encoding="utf-8"))
        for item in task4:
            self.assertEqual(text.count(f"`{item['question_id']}`"), 1)
        self.assertIn("英文原题", text)
        self.assertIn("中文审定题干", text)
        self.assertIn("核验答案", text)
        self.assertIn("教材例题（8题）", text)
        self.assertIn("应试训练（14题）", text)
        self.assertIn("甲部特训（17题）", text)
        self.assertIn("乙部特训（6题）", text)

    def test_report_and_state_preserve_scope_boundary(self):
        report = self.paths["report"].read_text(encoding="utf-8")
        state = self.paths["project_state"].read_text(encoding="utf-8")
        for required in ["V1.17", "45/45", "P0=0", "SQLite", "CSV", "59"]:
            self.assertIn(required, report)
        self.assertIn("其余452道", report)
        self.assertIn("当前正式数据版本：Joy DSE M2 题库 V1.17", state)
        self.assertIn("Task 5：微分应用45题正式迁移（已完成）", state)
        self.assertIn("其余452道完整题尚未迁移", state)
        self.assertNotIn("当前唯一优先任务：Joy 审批微分应用45题 Task 4", state)

    def test_manifest_hashes_and_source_provenance(self):
        manifest = json.loads(self.paths["manifest"].read_text(encoding="utf-8"))
        self.assertEqual(manifest["release_version"], "V1.17")
        self.assertEqual(manifest["baseline_v116_sqlite_sha256"], "d647244f54e9e54b25ec4885f16c47171c7521552876a5fa925a16d65d8c7714")
        self.assertEqual(manifest["approved_question_count"], 45)
        for name, expected_hash in manifest["artifact_sha256"].items():
            path = self.out / name
            self.assertTrue(path.is_file(), name)
            self.assertEqual(sha256(path), expected_hash, name)

    def test_second_build_is_byte_deterministic(self):
        from build_task5_release import build_release

        with tempfile.TemporaryDirectory() as temp2:
            other = build_release(Path(temp2) / "release")
            for key in ["sqlite", "csv", "knowledge", "report", "project_state", "approved_json", "taxonomy"]:
                self.assertEqual(sha256(self.paths[key]), sha256(other[key]), key)

    def test_release_package_is_deterministic_and_self_contained(self):
        from build_task5_release import package_release

        package_one = self.out.parent / "release-one.zip"
        package_two = self.out.parent / "release-two.zip"
        package_release(self.out, package_one)
        package_release(self.out, package_two)
        self.assertEqual(sha256(package_one), sha256(package_two))
        with zipfile.ZipFile(package_one) as archive:
            names = archive.namelist()
            self.assertIn("01_数据/Joy_M2_Complete_Question_DB_V1_17.sqlite3", names)
            self.assertIn("01_数据/Joy_M2_Complete_Questions_V1_17.csv", names)
            self.assertIn("02_知识文档/Joy_M2_微分应用45题_知识文档_V1.17.md", names)
            self.assertIn("03_报告/Joy_M2_V1.17_正式入库报告.md", names)
            self.assertIn("03_报告/PROJECT_STATE.md", names)
            self.assertIn("05_构建与测试/build_task5_release.py", names)
            self.assertIn("05_构建与测试/test_task5_import.py", names)
            self.assertIn("SHA256SUMS.txt", names)
            self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
