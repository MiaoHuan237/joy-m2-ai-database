from collections import Counter
from copy import deepcopy
import hashlib
from pathlib import Path


def _question_status(checks):
    allowed = {
        "question_boundary": {"pass"},
        "english_text": {"pass"},
        "chinese_text": {"pass", "revised"},
        "subparts_and_marks": {"pass", "unknown"},
    }
    return (
        "checked_pass"
        if all(checks.get(key) in values for key, values in allowed.items())
        else "needs_correction"
    )


def merge_review_records(baseline_records, review_records, *, audited_at):
    baseline_by_id = {row["question_id"]: row for row in baseline_records}
    review_by_id = {row["question_id"]: row for row in review_records}
    if set(baseline_by_id) != set(review_by_id):
        missing = sorted(set(baseline_by_id) - set(review_by_id))
        extra = sorted(set(review_by_id) - set(baseline_by_id))
        raise ValueError(f"review inventory mismatch: missing={missing}, extra={extra}")

    merged = []
    for base in baseline_records:
        row = deepcopy(base)
        review = review_by_id[base["question_id"]]
        checks = deepcopy(review["checks"])
        row.update(
            {
                "question_text_zh_reviewed": review["question_text_zh_reviewed"],
                "solution_verified": review["solution_verified"],
                "answer_status": review["answer_status_reviewed"],
                "answer_verification_status": review["answer_verification_status"],
                "primary_type": review["primary_type"],
                "tags": deepcopy(review["tags"]),
                "difficulty_level": review["difficulty_level"],
                "difficulty_dimensions": deepcopy(review["difficulty_dimensions"]),
                "difficulty_evidence": review["difficulty_evidence"],
                "correction_status": review["correction_status"],
                "corrections": deepcopy(review["corrections"]),
                "duplicate_status": review["duplicate_status"],
                "duplicate_reference": review["duplicate_reference"],
                "duplicate_evidence": review["duplicate_evidence"],
                "unresolved_issues": deepcopy(review["unresolved_issues"]),
                "audit_notes": review["audit_notes"],
                "review_checks": checks,
                "question_review_status": _question_status(checks),
                "formula_review_status": (
                    "checked_pass"
                    if checks.get("formula_symbols_units") == "pass"
                    else "needs_correction"
                ),
                "image_review_status": (
                    "not_required"
                    if checks.get("necessary_images") == "not_required"
                    else (
                        "checked_pass"
                        if checks.get("necessary_images") == "pass"
                        else "needs_correction"
                    )
                ),
                "answer_review_status": review["answer_verification_status"],
                "record_status": review["record_status"],
                "audited_at": audited_at,
            }
        )
        merged.append(row)
    return merged


def _issue(rule_id, question_id, evidence, action):
    return {
        "rule_id": rule_id,
        "severity": "P0",
        "question_id": question_id,
        "evidence": evidence,
        "action": action,
    }


def validate_review_records(rows, *, expected_ids, primary_types, tags):
    issues = []
    ids = [row.get("question_id") for row in rows]
    if set(ids) != set(expected_ids) or len(rows) != len(expected_ids):
        issues.append(
            _issue(
                "P0-COUNT-001",
                "PACKAGE",
                f"expected={len(expected_ids)}, actual={len(rows)}, inventory_match={set(ids) == set(expected_ids)}",
                "恢复完整且准确的题目清单。",
            )
        )
    if len(set(ids)) != len(ids):
        issues.append(
            _issue("P0-COUNT-002", "PACKAGE", "question_id重复", "删除重复记录并恢复缺失ID。")
        )

    primary_set = set(primary_types)
    tag_set = set(tags)
    check_values = {
        "question_boundary": {"pass", "issue"},
        "english_text": {"pass", "issue"},
        "chinese_text": {"pass", "revised", "issue"},
        "formula_symbols_units": {"pass", "issue"},
        "subparts_and_marks": {"pass", "unknown", "issue"},
        "necessary_images": {"pass", "not_required", "issue"},
        "answer_pairing": {"pass", "missing", "issue"},
        "answer_mathematics": {"pass", "needs_correction", "blocked"},
    }
    dimension_keys = {"概念数", "推理链长度", "建模强度", "代数负担", "条件处理", "易错风险"}
    answer_statuses = {
        "source_provided",
        "missing_from_source",
        "web_found_verified",
        "ai_solved_verified",
        "generated_unverified",
    }
    answer_verification_statuses = {
        "checked_pass",
        "needs_correction",
        "corrected_verified",
        "not_checked",
    }
    correction_statuses = {"none", "suspected", "confirmed", "corrected_verified"}
    duplicate_statuses = {"new", "adapted", "historical_reference", "exact_duplicate"}
    record_statuses = {"audit_passed", "audit_pending", "blocked", "approved_for_import"}
    correction_fields = {
        "question_text_zh",
        "question_text_original",
        "solution_original",
        "marks_total",
        "image_paths",
        "source_file/source_member",
        "solution_source_file/solution_source_member",
        "source_member_sha256",
        "solution_source_member_sha256",
    }
    correction_origins = {
        "mathpix_conversion",
        "source_original",
        "database_mapping",
        "translation",
    }
    correction_required_fields = {
        "field",
        "error_origin",
        "original",
        "corrected",
        "reason",
        "evidence",
    }
    required_fields = {
        "question_id",
        "source_section",
        "question_text_zh_reviewed",
        "solution_verified",
        "answer_verification_status",
        "primary_type",
        "tags",
        "difficulty_level",
        "difficulty_dimensions",
        "difficulty_evidence",
        "correction_status",
        "corrections",
        "duplicate_status",
        "duplicate_reference",
        "duplicate_evidence",
        "unresolved_issues",
        "audit_notes",
        "record_status",
    }
    for row in rows:
        question_id = row.get("question_id", "UNKNOWN")
        missing_fields = sorted(required_fields - set(row))
        if missing_fields:
            issues.append(
                _issue(
                    "P0-REVIEW-001",
                    question_id,
                    f"missing_fields={missing_fields}",
                    "补齐逐题复核契约字段。",
                )
            )
        checks = row.get("checks", row.get("review_checks", {}))
        invalid_checks = {
            key: checks.get(key)
            for key, allowed_values in check_values.items()
            if checks.get(key) not in allowed_values
        }
        if invalid_checks or set(checks) != set(check_values):
            issues.append(
                _issue(
                    "P0-REVIEW-002",
                    question_id,
                    f"invalid_checks={invalid_checks}, keys={sorted(checks)}",
                    "按逐题复核契约修正检查项及枚举值。",
                )
            )
        answer_status = row.get("answer_status_reviewed", row.get("answer_status"))
        if answer_status not in answer_statuses:
            issues.append(
                _issue(
                    "P0-ANSWER-003",
                    question_id,
                    f"answer_status={answer_status}",
                    "补齐答案状态并改用逐题复核契约枚举。",
                )
            )
        answer_verification_status = row.get("answer_verification_status")
        if answer_verification_status not in answer_verification_statuses:
            issues.append(
                _issue(
                    "P0-ANSWER-004",
                    question_id,
                    f"answer_verification_status={answer_verification_status}",
                    "改用逐题复核契约中的答案复核状态。",
                )
            )
        correction_status = row.get("correction_status")
        corrections = row.get("corrections")
        correction_status_invalid = correction_status not in correction_statuses
        correction_count_invalid = (
            not isinstance(corrections, list)
            or (correction_status == "none" and bool(corrections))
            or (correction_status in {"suspected", "confirmed", "corrected_verified"} and not corrections)
        )
        if correction_status_invalid or correction_count_invalid:
            issues.append(
                _issue(
                    "P0-CORRECTION-001",
                    question_id,
                    f"correction_status={correction_status}, corrections_type={type(corrections).__name__}",
                    "修正校订状态枚举，并使状态与校订项目数量一致。",
                )
            )
        invalid_corrections = []
        if isinstance(corrections, list):
            for index, correction in enumerate(corrections):
                if not isinstance(correction, dict):
                    invalid_corrections.append(f"corrections[{index}]不是对象")
                    continue
                missing = sorted(correction_required_fields - set(correction))
                empty = sorted(
                    key
                    for key in correction_required_fields & set(correction)
                    if correction.get(key) is None
                    or (isinstance(correction.get(key), str) and not correction.get(key).strip())
                )
                invalid_field = correction.get("field") not in correction_fields
                invalid_origin = correction.get("error_origin") not in correction_origins
                if missing or empty or invalid_field or invalid_origin:
                    invalid_corrections.append(
                        f"corrections[{index}]: missing={missing}, empty={empty}, "
                        f"field={correction.get('field')}, origin={correction.get('error_origin')}"
                    )
        if invalid_corrections:
            issues.append(
                _issue(
                    "P0-CORRECTION-002",
                    question_id,
                    "；".join(invalid_corrections),
                    "按契约补齐校订对象并改用受控字段与错误来源。",
                )
            )
        if row.get("duplicate_status") not in duplicate_statuses:
            issues.append(
                _issue(
                    "P0-DUPLICATE-001",
                    question_id,
                    f"duplicate_status={row.get('duplicate_status')}",
                    "改用逐题复核契约中的重复关系状态。",
                )
            )
        if row.get("primary_type") not in primary_set:
            issues.append(
                _issue("P0-CLASS-002", question_id, str(row.get("primary_type")), "改用受控主类型。")
            )
        illegal = sorted(set(row.get("tags", [])) - tag_set)
        if illegal:
            issues.append(
                _issue("P0-CLASS-003", question_id, f"illegal_tags={illegal}", "移除或映射非法标签。")
            )
        level = row.get("difficulty_level")
        if not isinstance(level, int) or not 1 <= level <= 5:
            issues.append(
                _issue("P0-CLASS-001", question_id, f"difficulty_level={level}", "按Joy Level 1–5重新评级。")
            )
        dimensions = row.get("difficulty_dimensions", {})
        if set(dimensions) != dimension_keys or any(
            not isinstance(value, int) or not 0 <= value <= 2 for value in dimensions.values()
        ):
            issues.append(
                _issue(
                    "P0-CLASS-004",
                    question_id,
                    f"difficulty_dimensions={dimensions}",
                    "六个难度维度必须齐全且每项为0、1或2。",
                )
            )
        if row.get("record_status") not in record_statuses:
            issues.append(
                _issue(
                    "P0-LIFE-002",
                    question_id,
                    f"record_status={row.get('record_status')}",
                    "改用合法审计生命周期状态。",
                )
            )
        if row.get("record_status") == "approved_for_import":
            issues.append(
                _issue("P0-LIFE-001", question_id, "Joy确认前出现approved_for_import", "恢复为审计状态。")
            )
        if row.get("record_status") == "audit_passed":
            actionable = any(
                value in {"issue", "needs_correction", "blocked", "not_checked"}
                for value in checks.values()
            )
            if actionable or not row.get("tags") or row.get("unresolved_issues"):
                issues.append(
                    _issue(
                        "P0-LIFE-003",
                        question_id,
                        "audit_passed与检查项、标签或未决事项不一致",
                        "改为audit_pending或关闭全部问题后再通过。",
                    )
                )
    return issues


def build_precheck_summary(rows):
    def counts(field):
        return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))

    answer_statuses = Counter(
        str(row.get("answer_status_reviewed", row.get("answer_status"))) for row in rows
    )
    return {
        "total": len(rows),
        "record_status": counts("record_status"),
        "difficulty_level": counts("difficulty_level"),
        "primary_type": counts("primary_type"),
        "answer_status": dict(sorted(answer_statuses.items())),
        "duplicate_status": counts("duplicate_status"),
        "correction_records": sum(bool(row.get("corrections")) for row in rows),
        "correction_items": sum(len(row.get("corrections", [])) for row in rows),
        "unresolved_question_count": sum(bool(row.get("unresolved_issues")) for row in rows),
    }


def verify_hash_baseline(root, baseline):
    root = Path(root)
    issues = []
    for expected in baseline.get("files", []):
        path = root / expected["path"]
        if not path.is_file():
            issues.append(
                _issue(
                    "P0-NONMUTATION-001",
                    "PACKAGE",
                    f"missing protected file: {expected['path']}",
                    "恢复受保护文件并停止写入正式数据。",
                )
            )
            continue
        data = path.read_bytes()
        actual_hash = hashlib.sha256(data).hexdigest()
        if len(data) != expected["bytes"] or actual_hash != expected["sha256"]:
            issues.append(
                _issue(
                    "P0-NONMUTATION-001",
                    "PACKAGE",
                    (
                        f"{expected['path']}: expected bytes/hash "
                        f"{expected['bytes']}/{expected['sha256']}, actual {len(data)}/{actual_hash}"
                    ),
                    "停止任务并从冻结事实源恢复受保护文件。",
                )
            )
    return issues


def _review_issue(rule_id, question_id, evidence, action):
    return {
        "rule_id": rule_id,
        "severity": "P1",
        "question_id": question_id,
        "evidence": evidence,
        "action": action,
    }


def build_validation_report(
    rows,
    *,
    expected_ids,
    primary_types,
    tags,
    expected_sections,
    hash_issues,
):
    issues = list(hash_issues)
    issues.extend(
        validate_review_records(
            rows,
            expected_ids=expected_ids,
            primary_types=primary_types,
            tags=tags,
        )
    )

    actual_sections = Counter(row.get("source_section") for row in rows)
    if dict(actual_sections) != dict(expected_sections):
        issues.append(
            _issue(
                "P0-COUNT-003",
                "PACKAGE",
                f"expected sections={dict(expected_sections)}, actual={dict(actual_sections)}",
                "恢复8/14/17/6来源分布。",
            )
        )
    for row in rows:
        question_id = row.get("question_id", "UNKNOWN")
        checks = row.get("checks", row.get("review_checks", {}))
        if row.get("record_status") == "audit_pending":
            issues.append(
                _review_issue(
                    "P1-AUDIT-001",
                    question_id,
                    "record_status=audit_pending",
                    "关闭校订或待确认问题后再改为audit_passed。",
                )
            )
        if row.get("unresolved_issues"):
            issues.append(
                _review_issue(
                    "P1-UNRESOLVED-001",
                    question_id,
                    "；".join(row["unresolved_issues"]),
                    "由Joy确认或退回修订。",
                )
            )
        if not row.get("tags"):
            issues.append(
                _review_issue(
                    "P1-CLASS-001",
                    question_id,
                    "tags为空，现有受控词表可能缺少适用标签",
                    "补充准确受控标签或经Joy确认扩展词表。",
                )
            )

        actionable_checks = {
            key: value
            for key, value in checks.items()
            if value in {"issue", "missing", "needs_correction", "blocked", "not_checked"}
        }
        if actionable_checks:
            issues.append(
                _review_issue(
                    "P1-CHECK-001",
                    question_id,
                    ", ".join(f"{key}={value}" for key, value in sorted(actionable_checks.items())),
                    "按逐题校订记录关闭对应检查项后再入库。",
                )
            )
        if checks.get("subparts_and_marks") == "issue":
            issues.append(
                _review_issue(
                    "P1-MARKS-001",
                    question_id,
                    "subparts_and_marks=issue",
                    "依据冻结来源补录或订正分值，并保留证据。",
                )
            )
        source_mapping_corrections = [
            item
            for item in row.get("corrections", [])
            if item.get("field")
            in {
                "source_file/source_member",
                "solution_source_file/solution_source_member",
                "source_member_sha256",
                "solution_source_member_sha256",
            }
            and item.get("error_origin") == "database_mapping"
        ]
        if source_mapping_corrections:
            issues.append(
                _review_issue(
                    "P1-SOURCE-001",
                    question_id,
                    "；".join(item.get("corrected", "") for item in source_mapping_corrections),
                    "Joy确认后再将正确来源映射写入候选入库记录。",
                )
            )
        if row.get("duplicate_status") in {"adapted", "historical_reference", "exact_duplicate"} and not str(
            row.get("duplicate_reference", "")
        ).strip():
            issues.append(
                _review_issue(
                    "P1-DUPLICATE-001",
                    question_id,
                    f"duplicate_status={row.get('duplicate_status')}但duplicate_reference为空",
                    "填写可追溯的相关题ID，或改为new并说明依据。",
                )
            )

    severity_counts = Counter(item["severity"] for item in issues)
    status = "FAIL" if severity_counts["P0"] else ("PASS_WITH_REVIEW" if issues else "PASS")
    return {
        "status": status,
        "summary": {
            "total": len(rows),
            "p0": severity_counts["P0"],
            "p1": severity_counts["P1"],
            "p2": severity_counts["P2"],
        },
        "issues": issues,
        "distribution": build_precheck_summary(rows),
    }


def _markdown_counts(mapping):
    return "、".join(f"{key}={value}" for key, value in mapping.items()) or "无"


def render_precheck_report(rows, validation_report, *, audited_at):
    distribution = validation_report["distribution"]
    summary = validation_report["summary"]
    pending = [row for row in rows if row.get("record_status") != "audit_passed"]
    correction_origins = Counter(
        item.get("error_origin", "未标明")
        for row in rows
        for item in row.get("corrections", [])
    )
    lines = [
        "# Joy_M2 微分应用45题入库预检报告",
        "",
        f"- 审计日期：{audited_at}",
        f"- 自动验收：`{validation_report['status']}`",
        f"- P0：{summary['p0']}；P1：{summary['p1']}；P2：{summary['p2']}",
        "- 生命周期边界：**Joy 确认前不得正式入库**；本报告及候选数据不会改写正式 SQLite/CSV。",
        "",
        "## 总体结论",
        "",
        f"本次逐题复核覆盖 {distribution['total']} 道完整题。"
        f"记录状态为 {_markdown_counts(distribution['record_status'])}。"
        "P0 为 0 仅表示事实源、题量和受控字段未出现阻断性错误；"
        "仍需关闭全部 P1 与 Joy 决策项后，才能生成正式导入候选。",
        "",
        "## 分布摘要",
        "",
        "| 项目 | 分布 |",
        "|---|---|",
        f"| Level | {_markdown_counts(distribution['difficulty_level'])} |",
        f"| 主类型 | {_markdown_counts(distribution['primary_type'])} |",
        f"| 答案状态 | {_markdown_counts(distribution['answer_status'])} |",
        f"| 重复关系 | {_markdown_counts(distribution['duplicate_status'])} |",
        f"| 含校订记录题数 | {distribution['correction_records']} |",
        f"| 校订项总数 | {distribution['correction_items']} |",
        f"| 含未关闭疑点题数 | {distribution['unresolved_question_count']} |",
        f"| 校订来源类型 | {_markdown_counts(dict(sorted(correction_origins.items())))} |",
        "",
        "## 待确认题目",
        "",
        "| 题目ID | 来源组 | 状态 | 待确认内容 |",
        "|---|---|---|---|",
    ]
    if pending:
        for row in pending:
            checks = row.get("checks", row.get("review_checks", {}))
            check_issues = [
                f"{key}={value}"
                for key, value in checks.items()
                if value in {"issue", "missing", "needs_correction", "blocked", "not_checked"}
            ]
            details = list(row.get("unresolved_issues", [])) + check_issues
            if not details and row.get("corrections"):
                details.append("校订记录待确认")
            safe_details = "；".join(details).replace("|", "\\|") or "状态待关闭"
            lines.append(
                f"| {row.get('question_id')} | {row.get('source_section')} | "
                f"{row.get('record_status')} | {safe_details} |"
            )
    else:
        lines.append("| 无 | — | — | — |")

    empty_tag_ids = [row.get("question_id") for row in rows if not row.get("tags")]
    source_mapping_ids = [
        row.get("question_id")
        for row in rows
        if any(
            item.get("field") in {
                "source_file/source_member",
                "solution_source_file/solution_source_member",
                "source_member_sha256",
                "solution_source_member_sha256",
            }
            and item.get("error_origin") == "database_mapping"
            for item in row.get("corrections", [])
        )
    ]
    lines.extend(
        [
            "",
            "## Joy 决策项",
            "",
            f"1. 确认或退回 {len(pending)} 道 `audit_pending/blocked` 题目的校订。",
            f"2. 确认 {len(source_mapping_ids)} 道来源映射校订后，才可更新候选记录的来源字段。",
            (
                "3. 决定是否扩展受控标签词表；当前空标签题目："
                + ("、".join(empty_tag_ids) if empty_tag_ids else "无")
                + "。"
            ),
            "4. 通过上述决策后重新运行自动验收；不得直接把本阶段状态改为 `approved_for_import`。",
            "",
            "## 自动验收问题清单",
            "",
            "| 级别 | 规则 | 题目ID | 证据 | 后续动作 |",
            "|---|---|---|---|---|",
        ]
    )
    if validation_report["issues"]:
        for item in validation_report["issues"]:
            evidence = str(item.get("evidence", "")).replace("|", "\\|").replace("\n", " ")
            action = str(item.get("action", "")).replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {item.get('severity')} | {item.get('rule_id')} | "
                f"{item.get('question_id')} | {evidence} | {action} |"
            )
    else:
        lines.append("| — | — | — | 未发现问题 | — |")
    lines.extend(
        [
            "",
            "## 导入边界",
            "",
            "- 本次产物是审计候选，不是正式入库数据。",
            "- 英文原题、来源答案和冻结文件保持原样；所有订正以独立字段和校订记录保存。",
            "- 只有 Joy 明确确认后，才能生成下一版完整题数据库导入候选并再次验收。",
            "",
        ]
    )
    return "\n".join(lines)


def _display_check(value):
    return {
        "pass": "通过",
        "revised": "已规范",
        "issue": "有疑点",
        "unknown": "分值未知",
        "not_required": "不适用",
        "missing": "缺失",
        "needs_correction": "需订正",
        "blocked": "阻断",
    }.get(value, str(value or ""))


def review_to_csv_row(row, *, validation_status=None):
    checks = row.get("review_checks", {})
    corrections = row.get("corrections", [])
    return {
        "question_id": row.get("question_id"),
        "source_question_number": row.get("source_question_number"),
        "source_section": row.get("source_section"),
        "source_heading": row.get("source_heading"),
        "old_difficulty": row.get("old_difficulty"),
        "old_tags": "；".join(row.get("old_tags", [])),
        "answer_status": row.get("answer_status"),
        "marks_total": row.get("marks_total"),
        "image_paths": "；".join(item.get("path", "") for item in row.get("image_paths", [])),
        "duplicate_status": row.get("duplicate_status"),
        "duplicate_reference": row.get("duplicate_reference", ""),
        "题目边界完整": _display_check(checks.get("question_boundary")),
        "英文题干准确": _display_check(checks.get("english_text")),
        "中文题干自然且含义一致": _display_check(checks.get("chinese_text")),
        "公式符号单位准确": _display_check(checks.get("formula_symbols_units")),
        "小问顺序与分值完整": _display_check(checks.get("subparts_and_marks")),
        "必要图片正确": _display_check(checks.get("necessary_images")),
        "答案与题目对应": _display_check(checks.get("answer_pairing")),
        "答案数学复核结论": _display_check(checks.get("answer_mathematics")),
        "新主类型": row.get("primary_type"),
        "新标签": "；".join(row.get("tags", [])),
        "新Level": row.get("difficulty_level"),
        "判级证据": row.get("difficulty_evidence"),
        "疑点": "；".join(row.get("unresolved_issues", [])),
        "订正内容": "；".join(
            f"{item.get('field', '')}: {item.get('corrected', '')}" for item in corrections
        ),
        "订正证据": "；".join(item.get("evidence", item.get("reason", "")) for item in corrections),
        "复核状态": row.get("record_status"),
        "自动验收结果": validation_status or "待运行整体验收",
        "Joy审批状态": "未确认",
        "record_status": row.get("record_status"),
    }
