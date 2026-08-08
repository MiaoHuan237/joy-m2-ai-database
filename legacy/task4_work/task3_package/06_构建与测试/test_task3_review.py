import sys
import hashlib
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

try:
    from build_task3_review import (
        build_precheck_summary,
        build_validation_report,
        merge_review_records,
        render_precheck_report,
        review_to_csv_row,
        validate_review_records,
        verify_hash_baseline,
    )
except ImportError:
    build_precheck_summary = None
    build_validation_report = None
    merge_review_records = None
    render_precheck_report = None
    review_to_csv_row = None
    validate_review_records = None
    verify_hash_baseline = None


PRIMARY_TYPES = ["极值与曲线性质", "变率"]
TAGS = ["驻点", "相关变化率", "综合题目"]


def baseline(question_id, section, original="ORIGINAL EN", solution="SOURCE ANSWER"):
    return {
        "question_id": question_id,
        "source_section": section,
        "question_text_original": original,
        "question_text_zh": "旧中文",
        "solution_original": solution,
        "answer_status": "source_provided",
        "question_review_status": "not_checked",
        "formula_review_status": "not_checked",
        "image_review_status": "not_checked",
        "answer_review_status": "not_checked",
        "record_status": "audit_pending",
        "corrections": [],
        "tags": [],
    }


def review(question_id, section, *, status="audit_passed", unresolved=None):
    return {
        "question_id": question_id,
        "source_section": section,
        "checks": {
            "question_boundary": "pass",
            "english_text": "pass",
            "chinese_text": "revised",
            "formula_symbols_units": "pass",
            "subparts_and_marks": "pass",
            "necessary_images": "not_required",
            "answer_pairing": "pass",
            "answer_mathematics": "pass",
        },
        "question_text_zh_reviewed": "新中文",
        "solution_verified": "VERIFIED ANSWER",
        "answer_status_reviewed": "source_provided",
        "answer_verification_status": "corrected_verified",
        "primary_type": "极值与曲线性质",
        "tags": ["驻点", "综合题目"],
        "difficulty_level": 4,
        "difficulty_dimensions": {
            "概念数": 2,
            "推理链长度": 2,
            "建模强度": 0,
            "代数负担": 1,
            "条件处理": 2,
            "易错风险": 2,
        },
        "difficulty_evidence": "需要多概念整合，评为L4。",
        "correction_status": "corrected_verified",
        "corrections": [
            {
                "field": "question_text_zh",
                "error_origin": "translation",
                "original": "旧中文",
                "corrected": "新中文",
                "reason": "术语规范",
                "evidence": "英中对照",
            }
        ],
        "duplicate_status": "new",
        "duplicate_reference": "",
        "duplicate_evidence": "未发现同题。",
        "unresolved_issues": unresolved or [],
        "audit_notes": "已复核",
        "record_status": status,
    }


class Task3ReviewTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(merge_review_records, "Task 3 merger is not implemented")
        self.assertIsNotNone(validate_review_records, "Task 3 validator is not implemented")
        self.assertIsNotNone(build_precheck_summary, "Task 3 summary is not implemented")
        self.assertIsNotNone(build_validation_report, "Task 3 report builder is not implemented")
        self.assertIsNotNone(review_to_csv_row, "Task 3 CSV mapping is not implemented")
        self.assertIsNotNone(verify_hash_baseline, "Task 3 hash verifier is not implemented")
        self.assertIsNotNone(render_precheck_report, "Task 3 precheck renderer is not implemented")

    def test_merge_preserves_source_text_and_adds_reviewed_fields(self):
        base = [baseline("Q1", "教材例题")]
        merged = merge_review_records(base, [review("Q1", "教材例题")], audited_at="2026-08-03")
        self.assertEqual(len(merged), 1)
        row = merged[0]
        self.assertEqual(row["question_text_original"], "ORIGINAL EN")
        self.assertEqual(row["solution_original"], "SOURCE ANSWER")
        self.assertEqual(row["question_text_zh_reviewed"], "新中文")
        self.assertEqual(row["solution_verified"], "VERIFIED ANSWER")
        self.assertEqual(row["primary_type"], "极值与曲线性质")
        self.assertEqual(row["difficulty_level"], 4)
        self.assertEqual(row["question_review_status"], "checked_pass")
        self.assertEqual(row["formula_review_status"], "checked_pass")
        self.assertEqual(row["image_review_status"], "not_required")
        self.assertEqual(row["answer_review_status"], "corrected_verified")
        self.assertEqual(row["record_status"], "audit_passed")

    def test_validator_rejects_duplicate_illegal_tag_and_approval(self):
        rows = [review("Q1", "教材例题"), review("Q1", "教材例题")]
        rows[0]["tags"] = ["非法标签"]
        rows[1]["record_status"] = "approved_for_import"
        issues = validate_review_records(
            rows,
            expected_ids={"Q1", "Q2"},
            primary_types=PRIMARY_TYPES,
            tags=TAGS,
        )
        codes = {item["rule_id"] for item in issues}
        self.assertEqual(
            codes,
            {"P0-COUNT-001", "P0-COUNT-002", "P0-CLASS-003", "P0-LIFE-001"},
        )

    def test_validator_rejects_invalid_contract_and_false_pass(self):
        row = review("Q1", "教材例题")
        row["checks"]["english_text"] = "unknown"
        row["difficulty_dimensions"]["易错风险"] = 3
        row["tags"] = []
        row["unresolved_issues"] = ["未关闭"]
        issues = validate_review_records(
            [row],
            expected_ids={"Q1"},
            primary_types=PRIMARY_TYPES,
            tags=TAGS,
        )
        self.assertEqual(
            {item["rule_id"] for item in issues},
            {
                "P0-REVIEW-002",
                "P0-CLASS-004",
                "P0-LIFE-003",
            },
        )

    def test_validator_rejects_invalid_status_enums_and_correction_contract(self):
        row = review("Q1", "教材例题", status="invalid_status")
        row["answer_status_reviewed"] = "invalid_answer_status"
        row["answer_verification_status"] = "invalid_verification_status"
        row["correction_status"] = "invalid_correction_status"
        row["duplicate_status"] = "invalid_duplicate_status"
        row["corrections"][0]["field"] = "invalid_field"
        row["corrections"][0]["error_origin"] = "invalid_origin"
        row["corrections"][0].pop("evidence")
        issues = validate_review_records(
            [row],
            expected_ids={"Q1"},
            primary_types=PRIMARY_TYPES,
            tags=TAGS,
        )
        self.assertEqual(
            {item["rule_id"] for item in issues},
            {
                "P0-ANSWER-003",
                "P0-ANSWER-004",
                "P0-CORRECTION-001",
                "P0-CORRECTION-002",
                "P0-DUPLICATE-001",
                "P0-LIFE-002",
            },
        )

    def test_validator_requires_reviewed_or_merged_answer_status(self):
        row = review("Q1", "教材例题")
        row.pop("answer_status_reviewed")
        issues = validate_review_records(
            [row],
            expected_ids={"Q1"},
            primary_types=PRIMARY_TYPES,
            tags=TAGS,
        )
        self.assertIn("P0-ANSWER-003", {item["rule_id"] for item in issues})

    def test_summary_counts_status_levels_types_and_corrections(self):
        rows = [
            review("Q1", "教材例题", status="audit_passed"),
            review("Q2", "应试训练", status="audit_pending", unresolved=["来源映射待修"]),
        ]
        rows[1]["primary_type"] = "变率"
        rows[1]["tags"] = ["相关变化率"]
        rows[1]["difficulty_level"] = 3
        rows[1]["corrections"] = []
        summary = build_precheck_summary(rows)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["record_status"], {"audit_passed": 1, "audit_pending": 1})
        self.assertEqual(summary["difficulty_level"], {"3": 1, "4": 1})
        self.assertEqual(summary["primary_type"], {"变率": 1, "极值与曲线性质": 1})
        self.assertEqual(summary["correction_records"], 1)
        self.assertEqual(summary["unresolved_question_count"], 1)

    def test_validation_report_is_pass_with_review_for_pending_record(self):
        rows = [
            review("Q1", "教材例题", status="audit_passed"),
            review("Q2", "应试训练", status="audit_pending", unresolved=["来源映射待修"]),
        ]
        rows[1]["primary_type"] = "变率"
        rows[1]["tags"] = ["相关变化率"]
        report = build_validation_report(
            rows,
            expected_ids={"Q1", "Q2"},
            primary_types=PRIMARY_TYPES,
            tags=TAGS,
            expected_sections={"教材例题": 1, "应试训练": 1},
            hash_issues=[],
        )
        self.assertEqual(report["status"], "PASS_WITH_REVIEW")
        self.assertEqual(report["summary"]["p0"], 0)
        self.assertEqual(report["summary"]["p1"], 2)
        self.assertEqual(
            {item["rule_id"] for item in report["issues"]},
            {"P1-AUDIT-001", "P1-UNRESOLVED-001"},
        )

    def test_validation_report_surfaces_check_marks_and_source_mapping_risks(self):
        row = review("Q1", "应试训练", status="audit_pending", unresolved=["来源映射待修"])
        row["checks"]["subparts_and_marks"] = "issue"
        row["checks"]["answer_mathematics"] = "needs_correction"
        row["corrections"] = [
            {
                "field": "solution_source_file/solution_source_member",
                "error_origin": "database_mapping",
                "original": "wrong.mmd",
                "corrected": "answer.mmd",
                "reason": "答案实际位于另一成员",
                "evidence": "冻结来源行号",
            }
        ]
        report = build_validation_report(
            [row],
            expected_ids={"Q1"},
            primary_types=PRIMARY_TYPES,
            tags=TAGS,
            expected_sections={"应试训练": 1},
            hash_issues=[],
        )
        self.assertEqual(report["status"], "PASS_WITH_REVIEW")
        self.assertEqual(report["summary"]["p0"], 0)
        self.assertEqual(
            {item["rule_id"] for item in report["issues"]},
            {
                "P1-AUDIT-001",
                "P1-UNRESOLVED-001",
                "P1-CHECK-001",
                "P1-MARKS-001",
                "P1-SOURCE-001",
            },
        )

    def test_summary_accepts_merged_answer_status_field(self):
        merged = merge_review_records(
            [baseline("Q1", "教材例题")],
            [review("Q1", "教材例题")],
            audited_at="2026-08-03",
        )
        summary = build_precheck_summary(merged)
        self.assertEqual(summary["answer_status"], {"source_provided": 1})

    def test_hash_verifier_detects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "protected.txt"
            target.write_bytes(b"changed")
            baseline = {
                "files": [
                    {
                        "path": "protected.txt",
                        "bytes": 8,
                        "sha256": hashlib.sha256(b"original").hexdigest(),
                    }
                ]
            }
            issues = verify_hash_baseline(root, baseline)
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]["rule_id"], "P0-NONMUTATION-001")

    def test_csv_row_exposes_review_checks_and_never_approval(self):
        row = baseline("Q1", "教材例题")
        merged = merge_review_records([row], [review("Q1", "教材例题")], audited_at="2026-08-03")[0]
        csv_row = review_to_csv_row(merged, validation_status="PASS_WITH_REVIEW")
        self.assertEqual(csv_row["题目边界完整"], "通过")
        self.assertEqual(csv_row["中文题干自然且含义一致"], "已规范")
        self.assertEqual(csv_row["答案数学复核结论"], "通过")
        self.assertEqual(csv_row["新Level"], 4)
        self.assertEqual(csv_row["Joy审批状态"], "未确认")
        self.assertEqual(csv_row["record_status"], "audit_passed")
        self.assertEqual(csv_row["自动验收结果"], "PASS_WITH_REVIEW")

    def test_validation_report_flags_non_new_duplicate_without_reference(self):
        row = review("Q1", "教材例题", status="audit_pending")
        row["duplicate_status"] = "adapted"
        row["duplicate_reference"] = ""
        report = build_validation_report(
            [row],
            expected_ids={"Q1"},
            primary_types=PRIMARY_TYPES,
            tags=TAGS,
            expected_sections={"教材例题": 1},
            hash_issues=[],
        )
        self.assertIn("P1-DUPLICATE-001", {item["rule_id"] for item in report["issues"]})

    def test_precheck_report_states_non_import_boundary_and_lists_pending(self):
        rows = [
            review("Q1", "教材例题", status="audit_passed"),
            review("Q2", "应试训练", status="audit_pending", unresolved=["来源映射待修"]),
        ]
        rows[1]["primary_type"] = "变率"
        rows[1]["tags"] = ["相关变化率"]
        report = build_validation_report(
            rows,
            expected_ids={"Q1", "Q2"},
            primary_types=PRIMARY_TYPES,
            tags=TAGS,
            expected_sections={"教材例题": 1, "应试训练": 1},
            hash_issues=[],
        )
        markdown = render_precheck_report(rows, report, audited_at="2026-08-03")
        self.assertIn("Joy_M2 微分应用45题入库预检报告", markdown)
        self.assertIn("Joy 确认前不得正式入库", markdown)
        self.assertIn("P0：0", markdown)
        self.assertIn("Q2", markdown)


if __name__ == "__main__":
    unittest.main()
