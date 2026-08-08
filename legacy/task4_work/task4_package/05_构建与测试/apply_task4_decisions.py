import argparse
import csv
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path


ACTIONABLE_CHECKS = {"issue", "needs_correction", "blocked", "not_checked"}


def _changed(before, after, field):
    return before.get(field) != after.get(field)


def apply_decisions(records, taxonomy, decisions, *, processed_at):
    updated = deepcopy(records)
    updated_taxonomy = deepcopy(taxonomy)
    by_id = {row["question_id"]: row for row in updated}

    target_ids = set(decisions["target_question_ids"])
    pending_ids = {row["question_id"] for row in records if row["record_status"] == "audit_pending"}
    if target_ids != pending_ids:
        raise ValueError(
            f"Task 4 target mismatch: missing={sorted(pending_ids-target_ids)}, "
            f"extra={sorted(target_ids-pending_ids)}"
        )
    if decisions.get("formal_import_approved") is not False:
        raise ValueError("Task 4 cannot grant formal import approval")

    additions = decisions["taxonomy_additions"]
    tags = list(updated_taxonomy["tags"])
    for tag in additions:
        if tag not in tags:
            tags.append(tag)
    updated_taxonomy["tags"] = tags
    updated_taxonomy["version"] = "V1.1-Task4-candidate"
    updated_taxonomy["updated_at"] = processed_at
    updated_taxonomy["change_note"] = "补齐全局最小值、从基本原理求导和导数为正区间三个微分应用考法标签。"

    mapping = decisions["solution_mapping"]
    mapping_ids = set(mapping["question_ids"])
    if mapping_ids != {f"M2QD-DA-TRAIN-Q{i}" for i in range(1, 15)}:
        raise ValueError("solution mapping must cover TRAIN-Q1 through TRAIN-Q14 exactly")

    audit_log = []
    for question_id in decisions["target_question_ids"]:
        row = by_id[question_id]
        before = deepcopy(row)

        if question_id in mapping_ids:
            for field in (
                "solution_source_file",
                "solution_source_member",
                "solution_source_member_sha256",
            ):
                row[field] = mapping[field]

        if question_id in decisions["marks"]:
            row["marks_total"] = decisions["marks"][question_id]

        if question_id in decisions["tag_assignments"]:
            row["tags"] = list(decisions["tag_assignments"][question_id])

        checks = row["review_checks"]
        for check_name, value in decisions["check_closures"].get(question_id, {}).items():
            if check_name not in checks:
                raise ValueError(f"unknown check {check_name} for {question_id}")
            checks[check_name] = value

        row["unresolved_issues"] = []
        row["record_status"] = "audit_passed"
        row["joy_approval"] = ""
        row["approved_at"] = None
        row["audited_at"] = processed_at
        row["question_review_status"] = (
            "checked_pass"
            if not ACTIONABLE_CHECKS.intersection(
                {
                    checks["question_boundary"],
                    checks["english_text"],
                    checks["chinese_text"],
                    checks["subparts_and_marks"],
                }
            )
            else "needs_correction"
        )
        row["formula_review_status"] = (
            "checked_pass" if checks["formula_symbols_units"] == "pass" else "needs_correction"
        )
        row["image_review_status"] = (
            "not_required"
            if checks["necessary_images"] == "not_required"
            else "checked_pass"
        )
        if row.get("corrections"):
            row["correction_status"] = "corrected_verified"
        if checks["answer_mathematics"] == "pass":
            if row.get("corrections"):
                row["answer_verification_status"] = "corrected_verified"
                row["answer_review_status"] = "corrected_verified"
            else:
                row["answer_verification_status"] = "checked_pass"
                row["answer_review_status"] = "checked_pass"

        note = decisions["resolution_notes"].get(
            question_id,
            "已按Task 4核验并关闭来源映射、分值或内容待决项。",
        )
        row["task4_resolution"] = note
        row["task4_processed_at"] = processed_at
        row["audit_notes"] = f"{row.get('audit_notes', '').rstrip()} Task 4：{note}".strip()

        candidate_fields = (
            "solution_source_file",
            "solution_source_member",
            "solution_source_member_sha256",
            "marks_total",
            "tags",
            "review_checks",
            "unresolved_issues",
            "record_status",
            "correction_status",
            "answer_verification_status",
            "answer_review_status",
            "question_review_status",
            "formula_review_status",
        )
        changed_fields = [field for field in candidate_fields if _changed(before, row, field)]
        audit_log.append(
            {
                "question_id": question_id,
                "source_section": row["source_section"],
                "changed_fields": changed_fields,
                "resolution": note,
                "before_status": before["record_status"],
                "after_status": row["record_status"],
                "formal_import_approved": False,
            }
        )

    return updated, updated_taxonomy, audit_log


def validate_task4_candidate(records, taxonomy, *, expected_ids, decisions):
    issues = []
    ids = [row.get("question_id") for row in records]
    if len(records) != 45 or len(set(ids)) != 45 or set(ids) != set(expected_ids):
        issues.append({"severity": "P0", "rule": "T4-COUNT-001", "evidence": "45题清单不一致"})

    allowed_tags = set(taxonomy.get("tags", []))
    allowed_primary = set(taxonomy.get("primary_types", []))
    for row in records:
        qid = row.get("question_id", "UNKNOWN")
        if row.get("primary_type") not in allowed_primary:
            issues.append({"severity": "P0", "rule": "T4-TAXONOMY-001", "question_id": qid})
        illegal = sorted(set(row.get("tags", [])) - allowed_tags)
        if illegal or not row.get("tags"):
            issues.append(
                {"severity": "P0", "rule": "T4-TAXONOMY-002", "question_id": qid, "evidence": illegal}
            )
        if row.get("record_status") != "audit_passed":
            issues.append({"severity": "P1", "rule": "T4-STATUS-001", "question_id": qid})
        if row.get("unresolved_issues"):
            issues.append({"severity": "P1", "rule": "T4-UNRESOLVED-001", "question_id": qid})
        actionable = sorted(ACTIONABLE_CHECKS.intersection(row.get("review_checks", {}).values()))
        if actionable:
            issues.append(
                {"severity": "P1", "rule": "T4-CHECK-001", "question_id": qid, "evidence": actionable}
            )
        if row.get("record_status") == "approved_for_import" or row.get("joy_approval"):
            issues.append({"severity": "P0", "rule": "T4-APPROVAL-001", "question_id": qid})
        if row.get("approved_at") is not None:
            issues.append({"severity": "P0", "rule": "T4-APPROVAL-002", "question_id": qid})

    mapping = decisions["solution_mapping"]
    by_id = {row["question_id"]: row for row in records}
    for qid in mapping["question_ids"]:
        for field in (
            "solution_source_file",
            "solution_source_member",
            "solution_source_member_sha256",
        ):
            if by_id[qid].get(field) != mapping[field]:
                issues.append(
                    {"severity": "P0", "rule": "T4-SOURCE-001", "question_id": qid, "field": field}
                )
    for qid, marks in decisions["marks"].items():
        if by_id[qid].get("marks_total") != marks:
            issues.append({"severity": "P0", "rule": "T4-MARKS-001", "question_id": qid})
    for qid, expected_tags in decisions["tag_assignments"].items():
        if set(by_id[qid].get("tags", [])) != set(expected_tags):
            issues.append({"severity": "P0", "rule": "T4-TAGS-001", "question_id": qid})

    p0 = sum(item["severity"] == "P0" for item in issues)
    p1 = sum(item["severity"] == "P1" for item in issues)
    status = "TECHNICALLY_READY_FOR_JOY_APPROVAL" if p0 == 0 and p1 == 0 else "FAIL"
    return {
        "status": status,
        "summary": {
            "total": len(records),
            "unique_ids": len(set(ids)),
            "audit_passed": sum(row.get("record_status") == "audit_passed" for row in records),
            "approved_for_import": sum(
                row.get("record_status") == "approved_for_import" for row in records
            ),
            "p0": p0,
            "p1": p1,
            "formal_import_approved": False,
        },
        "issues": issues,
        "boundary": "Task 4仅关闭技术审计项；仍需Joy明确批准后才能生成正式导入候选。",
    }


def _write_csv(path, records):
    fields = [
        "题目ID",
        "分区",
        "原题号",
        "总分",
        "主类型",
        "细分标签",
        "Level",
        "答案来源文件",
        "答案来源成员",
        "答案成员SHA256",
        "审计状态",
        "Task4处理结论",
        "Joy审批",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow(
                {
                    "题目ID": row["question_id"],
                    "分区": row["source_section"],
                    "原题号": row["source_question_number"],
                    "总分": row["marks_total"],
                    "主类型": row["primary_type"],
                    "细分标签": "；".join(row["tags"]),
                    "Level": row["difficulty_level"],
                    "答案来源文件": row["solution_source_file"],
                    "答案来源成员": row["solution_source_member"],
                    "答案成员SHA256": row["solution_source_member_sha256"],
                    "审计状态": row["record_status"],
                    "Task4处理结论": row.get("task4_resolution", "Task 3已通过"),
                    "Joy审批": "未批准",
                }
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--taxonomy", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--processed-at", default=datetime.now().astimezone().isoformat(timespec="seconds"))
    args = parser.parse_args()

    records = json.loads(args.records.read_text(encoding="utf-8"))
    taxonomy = json.loads(args.taxonomy.read_text(encoding="utf-8"))
    decisions = json.loads(args.decisions.read_text(encoding="utf-8"))
    updated, updated_taxonomy, audit_log = apply_decisions(
        records, taxonomy, decisions, processed_at=args.processed_at
    )
    validation = validate_task4_candidate(
        updated,
        updated_taxonomy,
        expected_ids={row["question_id"] for row in records},
        decisions=decisions,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "complete_questions_45_task4.json").write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "differentiation_application_taxonomy_v1.1_task4.json").write_text(
        json.dumps(updated_taxonomy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "task4_audit_log.json").write_text(
        json.dumps(audit_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "task4_validation_report.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _write_csv(args.output_dir / "微分应用45题_Task4审阅候选.csv", updated)
    print(json.dumps(validation, ensure_ascii=False))


if __name__ == "__main__":
    main()
