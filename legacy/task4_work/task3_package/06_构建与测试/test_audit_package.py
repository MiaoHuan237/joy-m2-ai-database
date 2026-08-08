import copy
import hashlib
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


AUDIT_ROOT = Path(__file__).resolve().parents[1]
TOOLS = AUDIT_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from build_audit_package import (  # noqa: E402
    ACCEPTANCE_RULES,
    DIFFICULTY_LEVELS,
    PRIMARY_TYPES,
    TAGS,
    classify_section,
    sha256_file,
    transform_complete_row,
)
from validate_audit_package import validate_protected_inputs, validate_records  # noqa: E402


class BuilderContractTests(unittest.TestCase):
    def test_sha256_file_matches_standard_library(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.bin"
            path.write_bytes(b"Joy M2 audit\n")
            self.assertEqual(
                sha256_file(path), hashlib.sha256(path.read_bytes()).hexdigest()
            )

    def test_section_mapping_has_expected_distribution(self):
        ids = (
            [f"M2QD-DA-EXAMPLE-Q{i}" for i in range(1, 9)]
            + [f"M2QD-DA-TRAIN-Q{i}" for i in range(1, 15)]
            + [f"M2QD-DA-PARTA-Q{i}" for i in range(1, 18)]
            + [f"M2QD-DA-PARTB-Q{i}" for i in range(1, 7)]
        )
        counts = Counter(classify_section(question_id, "") for question_id in ids)
        self.assertEqual(
            counts,
            {
                "教材例题": 8,
                "应试训练": 14,
                "甲部特训": 17,
                "乙部特训": 6,
            },
        )

    def test_transform_preserves_complete_question_and_sets_draft_lifecycle(self):
        row = {
            "question_id": "M2QD-DA-EXAMPLE-Q1",
            "parent_question_id": None,
            "source_id": "M2QD-DIFFERENTIATION-APPLICATIONS",
            "question_number": 1,
            "part_path": "",
            "record_kind": "complete",
            "is_complete_question": 1,
            "marks": 7,
            "marking_status": "published",
            "difficulty": 4,
            "difficulty_label": "Joy 教学难度 Level 4/5",
            "question_text_original": "Question (a) ... (b) ...",
            "question_text_zh": "题目（a）……（b）……",
            "question_latex": "Question (a) ... (b) ...",
            "official_marking_scheme": "Solution (a) ... (b) ...",
            "tags": "#切线 #参数",
            "source_file": "M2Quick Drill-微分法的应用.mmd.zip",
            "source_heading": "应试例题 3.1（完整题）",
            "source_pp_page": "",
            "source_ms_page": "",
            "image_paths": "[]",
            "raw_section": "raw",
        }
        source = {
            "source_sha256": "a" * 64,
            "official_marking_available": 0,
        }
        record = transform_complete_row(row, source, {})
        self.assertEqual(record["question_id"], row["question_id"])
        self.assertEqual(record["question_text_original"], row["question_text_original"])
        self.assertEqual(record["solution_original"], row["official_marking_scheme"])
        self.assertEqual(record["record_status"], "audit_pending")
        self.assertIsNone(record["difficulty_level"])
        self.assertEqual(record["old_difficulty"], 4)
        self.assertNotIn("record_kind", record)
        self.assertNotIn("parent_question_id", record)

    def test_transform_rejects_small_question_record(self):
        row = {
            "question_id": "M2QD-DA-EXAMPLE-Q1(a)",
            "parent_question_id": "M2QD-DA-EXAMPLE-Q1",
            "source_id": "M2QD-DIFFERENTIATION-APPLICATIONS",
            "part_path": "(a)",
            "is_complete_question": 0,
        }
        with self.assertRaises(ValueError):
            transform_complete_row(row, {}, {})


class ControlledVocabularyTests(unittest.TestCase):
    def test_primary_types_are_exactly_the_approved_five(self):
        self.assertEqual(
            PRIMARY_TYPES,
            ["切线与法线", "极值与曲线性质", "最值与最优化", "变率", "综合微分应用"],
        )

    def test_difficulty_levels_are_one_through_five(self):
        self.assertEqual([item["level"] for item in DIFFICULTY_LEVELS], [1, 2, 3, 4, 5])
        self.assertTrue(all(item["standard"] for item in DIFFICULTY_LEVELS))

    def test_tag_vocabulary_contains_required_application_tags(self):
        for tag in ["过指定点的切线", "拐点", "几何最优化", "相关变化率", "建立变量关系"]:
            self.assertIn(tag, TAGS)

    def test_acceptance_rules_cover_all_severities(self):
        severities = {rule["severity"] for rule in ACCEPTANCE_RULES}
        self.assertEqual(severities, {"P0", "P1", "P2"})
        self.assertEqual(len({rule["rule_id"] for rule in ACCEPTANCE_RULES}), len(ACCEPTANCE_RULES))


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.valid_record = {
            "question_id": "M2QD-DA-EXAMPLE-Q1",
            "source_id": "M2QD-DIFFERENTIATION-APPLICATIONS",
            "source_question_number": "EXAMPLE-Q1",
            "source_section": "教材例题",
            "source_file": "M2Quick Drill-微分法的应用.mmd.zip",
            "source_member": "example.mmd",
            "source_sha256": "a" * 64,
            "source_fragment_hash": "b" * 64,
            "question_text_original": "Complete question",
            "question_text_zh": "完整题目",
            "question_latex": "Complete question",
            "marks_total": 4,
            "image_paths": [],
            "solution_original": "Complete solution",
            "solution_verified": "",
            "answer_status": "source_provided",
            "answer_verification_status": "not_checked",
            "official_marking_available": False,
            "primary_type": "切线与法线",
            "tags": ["已知切点求切线"],
            "difficulty_level": 2,
            "difficulty_evidence": "常规两步切线题。",
            "correction_status": "none",
            "corrections": [],
            "duplicate_status": "new",
            "audit_notes": "",
            "record_status": "audit_passed",
            "joy_approval": "",
            "schema_version": "complete-question-v1.0-draft",
        }

    def test_valid_record_has_no_p0_issue(self):
        result = validate_records([self.valid_record], expected_count=1, root=AUDIT_ROOT)
        self.assertFalse(any(issue["severity"] == "P0" for issue in result["issues"]))

    def test_duplicate_id_is_p0(self):
        result = validate_records([self.valid_record, copy.deepcopy(self.valid_record)], expected_count=2, root=AUDIT_ROOT)
        self.assertIn("P0-COUNT-002", {issue["rule_id"] for issue in result["issues"]})

    def test_invalid_level_is_p0_for_audit_passed_record(self):
        record = copy.deepcopy(self.valid_record)
        record["difficulty_level"] = 9
        result = validate_records([record], expected_count=1, root=AUDIT_ROOT)
        self.assertIn("P0-CLASS-001", {issue["rule_id"] for issue in result["issues"]})

    def test_illegal_tag_is_p0_for_audit_passed_record(self):
        record = copy.deepcopy(self.valid_record)
        record["tags"] = ["非法标签"]
        result = validate_records([record], expected_count=1, root=AUDIT_ROOT)
        self.assertIn("P0-CLASS-003", {issue["rule_id"] for issue in result["issues"]})

    def test_source_provided_without_answer_is_p0(self):
        record = copy.deepcopy(self.valid_record)
        record["solution_original"] = ""
        result = validate_records([record], expected_count=1, root=AUDIT_ROOT)
        self.assertIn("P0-ANSWER-001", {issue["rule_id"] for issue in result["issues"]})

    def test_approved_without_joy_confirmation_is_p0(self):
        record = copy.deepcopy(self.valid_record)
        record["record_status"] = "approved_for_import"
        result = validate_records([record], expected_count=1, root=AUDIT_ROOT)
        self.assertIn("P0-LIFE-001", {issue["rule_id"] for issue in result["issues"]})

    def test_pending_record_with_blank_new_classification_is_review_not_p0(self):
        record = copy.deepcopy(self.valid_record)
        record["record_status"] = "audit_pending"
        record["primary_type"] = ""
        record["tags"] = []
        record["difficulty_level"] = None
        record["difficulty_evidence"] = ""
        result = validate_records([record], expected_count=1, root=AUDIT_ROOT)
        self.assertFalse(any(issue["severity"] == "P0" for issue in result["issues"]))
        self.assertIn("P1-AUDIT-001", {issue["rule_id"] for issue in result["issues"]})

    def test_protected_input_hash_change_is_p0(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            protected = workspace / "formal.sqlite3"
            protected.write_bytes(b"before")
            manifest = {
                "protected_inputs_before": [{
                    "path": "formal.sqlite3",
                    "bytes": len(b"before"),
                    "sha256": hashlib.sha256(b"before").hexdigest(),
                }]
            }
            self.assertEqual(validate_protected_inputs(manifest, workspace), [])
            protected.write_bytes(b"after")
            issues = validate_protected_inputs(manifest, workspace)
            self.assertEqual(issues[0]["rule_id"], "P0-NONMUTATION-001")


class GeneratedPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records_path = AUDIT_ROOT / "derived" / "complete_questions_45.json"

    def test_generated_package_has_exactly_45_unique_complete_questions(self):
        records = json.loads(self.records_path.read_text(encoding="utf-8"))
        self.assertEqual(len(records), 45)
        self.assertEqual(len({record["question_id"] for record in records}), 45)
        self.assertTrue(all(record["record_status"] == "audit_pending" for record in records))
        self.assertTrue(all("parent_question_id" not in record for record in records))

    def test_generated_section_distribution_matches_fact_source(self):
        records = json.loads(self.records_path.read_text(encoding="utf-8"))
        self.assertEqual(
            Counter(record["source_section"] for record in records),
            {"教材例题": 8, "应试训练": 14, "甲部特训": 17, "乙部特训": 6},
        )

    def test_no_record_is_approved_for_import(self):
        records = json.loads(self.records_path.read_text(encoding="utf-8"))
        self.assertNotIn("approved_for_import", {record["record_status"] for record in records})


if __name__ == "__main__":
    unittest.main()
