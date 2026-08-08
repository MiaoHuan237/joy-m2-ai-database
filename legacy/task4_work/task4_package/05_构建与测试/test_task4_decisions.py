import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
TASK4_WORK = HERE.parents[1]
TASK3_ROOT = TASK4_WORK / "task3_package"
sys.path.insert(0, str(HERE))

from apply_task4_decisions import apply_decisions, validate_task4_candidate


PACKAGE_INPUT = HERE.parent / "06_Task3输入"
if PACKAGE_INPUT.exists():
    RECORDS_PATH = PACKAGE_INPUT / "complete_questions_45_reviewed.json"
    TAXONOMY_PATH = PACKAGE_INPUT / "differentiation_application_taxonomy.json"
else:
    RECORDS_PATH = TASK3_ROOT / "03_候选数据" / "complete_questions_45_reviewed.json"
    TAXONOMY_PATH = TASK3_ROOT / "05_标准规则" / "differentiation_application_taxonomy.json"
DECISIONS_PATH = HERE / "task4_decisions.json"

TRAIN_IDS = [f"M2QD-DA-TRAIN-Q{i}" for i in range(1, 15)]
PENDING_IDS = {
    "M2QD-DA-EXAMPLE-Q3",
    "M2QD-DA-EXAMPLE-Q6",
    "M2QD-DA-EXAMPLE-Q8",
    *TRAIN_IDS,
    "M2QD-DA-PARTA-Q6",
    "M2QD-DA-PARTA-Q13",
    "M2QD-DA-PARTA-Q16",
    "M2QD-DA-PARTB-Q3",
}


class Task4DecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
        cls.taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
        cls.decisions = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
        cls.updated, cls.updated_taxonomy, cls.audit_log = apply_decisions(
            cls.records,
            cls.taxonomy,
            cls.decisions,
            processed_at="2026-08-08T20:00:00+08:00",
        )
        cls.by_id = {row["question_id"]: row for row in cls.updated}

    def test_task4_targets_exactly_the_21_pending_records(self):
        task3_pending = {
            row["question_id"] for row in self.records if row["record_status"] == "audit_pending"
        }
        self.assertEqual(task3_pending, PENDING_IDS)
        self.assertEqual(set(self.decisions["target_question_ids"]), PENDING_IDS)
        self.assertEqual({row["question_id"] for row in self.audit_log}, PENDING_IDS)

    def test_all_14_training_answers_use_the_verified_member_mapping(self):
        for question_id in TRAIN_IDS:
            row = self.by_id[question_id]
            self.assertEqual(row["solution_source_file"], "微分的应用甲部.mmd.zip")
            self.assertEqual(
                row["solution_source_member"],
                "c2e97ff4-9258-43ff-802f-ac95d2c5c0e2.mmd",
            )
            self.assertEqual(
                row["solution_source_member_sha256"],
                "bfd75702b5abff3f604bfeb722f6ab7cd6c23566d15ea550bbf05be1b4dbbeb0",
            )

    def test_only_the_three_supported_marks_are_filled(self):
        expected = {
            "M2QD-DA-TRAIN-Q3": 4,
            "M2QD-DA-TRAIN-Q7": 6,
            "M2QD-DA-TRAIN-Q13": 3,
        }
        for question_id, marks in expected.items():
            self.assertEqual(self.by_id[question_id]["marks_total"], marks)
        changed_mark_ids = {
            item["question_id"]
            for item in self.audit_log
            if "marks_total" in item["changed_fields"]
        }
        self.assertEqual(changed_mark_ids, set(expected))

    def test_taxonomy_and_two_gap_records_receive_precise_tags(self):
        required = {"全局最小值", "从基本原理求导", "导数为正区间"}
        self.assertTrue(required.issubset(set(self.updated_taxonomy["tags"])))
        self.assertIn("全局最小值", self.by_id["M2QD-DA-EXAMPLE-Q3"]["tags"])
        self.assertEqual(
            set(self.by_id["M2QD-DA-PARTA-Q13"]["tags"]),
            {"从基本原理求导", "导数为正区间"},
        )

    def test_all_21_records_close_actionable_checks_and_unresolved_items(self):
        blocked_values = {"issue", "needs_correction", "blocked", "not_checked"}
        for question_id in PENDING_IDS:
            row = self.by_id[question_id]
            self.assertEqual(row["record_status"], "audit_passed")
            self.assertEqual(row["unresolved_issues"], [])
            self.assertFalse(blocked_values.intersection(row["review_checks"].values()))

    def test_source_text_and_correction_history_are_preserved(self):
        before = {row["question_id"]: row for row in self.records}
        for question_id in PENDING_IDS:
            self.assertEqual(
                self.by_id[question_id]["question_text_original"],
                before[question_id]["question_text_original"],
            )
            self.assertEqual(
                self.by_id[question_id]["corrections"],
                before[question_id]["corrections"],
            )

    def test_candidate_is_never_approved_for_import(self):
        for row in self.updated:
            self.assertNotEqual(row["record_status"], "approved_for_import")
            self.assertEqual(row["joy_approval"], "")
            self.assertIsNone(row["approved_at"])

    def test_candidate_validation_is_clean_but_still_requires_joy_approval(self):
        report = validate_task4_candidate(
            self.updated,
            self.updated_taxonomy,
            expected_ids={row["question_id"] for row in self.records},
            decisions=self.decisions,
        )
        self.assertEqual(report["status"], "TECHNICALLY_READY_FOR_JOY_APPROVAL")
        self.assertEqual(report["summary"]["p0"], 0)
        self.assertEqual(report["summary"]["p1"], 0)
        self.assertEqual(report["summary"]["audit_passed"], 45)
        self.assertEqual(report["summary"]["approved_for_import"], 0)


if __name__ == "__main__":
    unittest.main()
