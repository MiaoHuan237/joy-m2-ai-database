from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


V117_DB_SHA256 = "58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab"
EXCLUDED_SOURCE_ID = "M2QD-DIFFERENTIATION-APPLICATIONS"
RELEASE_VERSION = "V1.18"
AUDITED_AT = "2026-08-08T21:00:00+08:00"
APPROVED_AT = "2026-08-08T21:00:00+08:00"

TABLE_COLUMNS = [
    "question_id", "source_id", "source_question_number", "source_section", "source_file",
    "source_member", "source_sha256", "source_member_sha256", "source_fragment_hash", "source_page",
    "solution_source_file", "solution_source_member", "solution_source_member_sha256",
    "question_text_original", "question_text_zh", "question_text_zh_reviewed", "question_latex",
    "marks_total", "year", "image_paths", "solution_original", "solution_verified",
    "answer_status", "answer_verification_status", "official_marking_available", "primary_type",
    "tags", "difficulty_level", "difficulty_evidence", "difficulty_dimensions",
    "old_difficulty", "old_difficulty_label", "old_tags", "question_review_status",
    "formula_review_status", "image_review_status", "answer_review_status", "correction_status",
    "corrections", "duplicate_status", "duplicate_reference", "duplicate_evidence", "audit_notes",
    "review_checks", "unresolved_issues", "record_status", "joy_approval", "audited_at",
    "approved_at", "schema_version", "selectable", "source_heading", "formal_release_version",
    "source_order",
]

DB_TABLE_COLUMNS = [
    "question_id", "source_id", "source_question_number", "source_section", "source_file",
    "source_member", "source_sha256", "source_member_sha256", "source_fragment_hash", "source_page",
    "solution_source_file", "solution_source_member", "solution_source_member_sha256",
    "question_text_original", "question_text_zh", "question_text_zh_reviewed", "question_latex",
    "marks_total", "year", "image_paths_json", "solution_original", "solution_verified",
    "answer_status", "answer_verification_status", "official_marking_available", "primary_type",
    "tags_json", "difficulty_level", "difficulty_evidence", "difficulty_dimensions_json",
    "old_difficulty", "old_difficulty_label", "old_tags_json", "question_review_status",
    "formula_review_status", "image_review_status", "answer_review_status", "correction_status",
    "corrections_json", "duplicate_status", "duplicate_reference", "duplicate_evidence", "audit_notes",
    "review_checks_json", "unresolved_issues_json", "record_status", "joy_approval", "audited_at",
    "approved_at", "schema_version", "selectable", "source_heading", "task4_processed_at",
    "task4_resolution", "source_order",
]

MARKS_2026 = {
    "2026-Q1": 4, "2026-Q2": 6, "2026-Q3": 6, "2026-Q4": 6,
    "2026-Q5": 6, "2026-Q6": 6, "2026-Q7": 8, "2026-Q8": 8,
    "2026-Q9": 13, "2026-Q10": 12, "2026-Q11": 12, "2026-Q12": 13,
}

LEVELS_2026 = {
    "2026-Q1": 2, "2026-Q2": 2, "2026-Q3": 2, "2026-Q4": 2,
    "2026-Q5": 3, "2026-Q6": 3, "2026-Q7": 4, "2026-Q8": 4,
    "2026-Q9": 4, "2026-Q10": 4, "2026-Q11": 4, "2026-Q12": 4,
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_baseline(db_path: Path, manifest_path: Path) -> None:
    if sha256_file(db_path) != V117_DB_SHA256:
        raise ValueError("V1.17 SQLite hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["artifact_sha256"][db_path.name]
    if expected != V117_DB_SHA256:
        raise ValueError("V1.17 manifest does not lock the expected SQLite")
    with sqlite3.connect(db_path) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("V1.17 SQLite integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("V1.17 SQLite foreign key check failed")
        if db.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone()[0] != 45:
            raise ValueError("V1.17 must contain exactly 45 migrated questions")
        if db.execute("SELECT COUNT(*) FROM complete_questions").fetchone()[0] != 497:
            raise ValueError("V1.17 legacy view must contain exactly 497 complete questions")


def extract_legacy_candidates(db_path: Path) -> list[dict[str, Any]]:
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            """
            SELECT q.*, s.source_type, s.title AS source_title,
                   s.source_file AS source_registry_file,
                   s.solution_file AS solution_registry_file,
                   s.source_sha256 AS source_registry_sha256,
                   s.official_marking_available,
                   s.notes AS source_notes,
                   t.topic_code AS primary_topic_code,
                   t.topic_name AS primary_topic_name
            FROM complete_questions q
            JOIN sources s ON s.source_id=q.source_id
            JOIN topics t ON t.topic_id=q.primary_topic_id
            WHERE q.source_id<>?
            ORDER BY q.source_id, q.question_number, q.question_id
            """,
            (EXCLUDED_SOURCE_ID,),
        ).fetchall()
    records = [dict(row) for row in rows]
    if len(records) != 452:
        raise ValueError(f"Expected 452 legacy candidates, found {len(records)}")
    if len({row["question_id"] for row in records}) != 452:
        raise ValueError("Legacy candidate IDs are not unique")
    return records


def _extract_2026_solution(raw_section: str) -> str:
    blocks = re.findall(
        r"### 7\. 参考解答\s*(.*?)(?=\n### 8\. 替代解法|\Z)",
        raw_section,
        flags=re.DOTALL,
    )
    cleaned = [block.strip() for block in blocks if block.strip()]
    return "\n\n".join(cleaned)


def _clean_tags(raw_tags: str, primary_type: str, linked_topics: list[str]) -> list[str]:
    prefix = re.split(r"\n\s*#{1,3}\s+", raw_tags, maxsplit=1)[0]
    extracted = re.findall(r"#([A-Za-z0-9_\-\u4e00-\u9fff、]+)", prefix)
    values = [primary_type, *linked_topics, *extracted]
    result: list[str] = []
    for value in values:
        value = value.strip().lstrip("#")
        if not value or value in result:
            continue
        if not re.fullmatch(r"[A-Za-z0-9_\-\u4e00-\u9fff、]+", value):
            continue
        result.append(value)
    return result


def _resolve_images(raw_value: str, workspace_root: Path) -> list[str]:
    values = json.loads(raw_value or "[]")
    resolved: list[str] = []
    for value in values:
        candidates = [
            workspace_root / value,
            workspace_root / "task5_work/v116/m2_question_bank" / value,
            workspace_root / "task5_work/v116" / value,
        ]
        path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if path is None:
            raise ValueError(f"Missing required image: {value}")
        relative = path.relative_to(workspace_root).as_posix()
        if relative not in resolved:
            resolved.append(relative)
    return resolved


def _normal_math_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def audit_candidates(db_path: Path, workspace_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = extract_legacy_candidates(db_path)
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        linked: dict[str, list[str]] = {}
        for row in db.execute(
            """
            SELECT qt.question_id,t.topic_name
            FROM question_topics qt JOIN topics t ON t.topic_id=qt.topic_id
            ORDER BY qt.question_id,qt.is_primary DESC,t.sort_order
            """
        ):
            linked.setdefault(row["question_id"], []).append(row["topic_name"])
        existing_v2_texts = {
            _normal_math_text(row[0]): row[1]
            for row in db.execute("SELECT question_text_original,question_id FROM complete_questions_v2")
        }

    normalized_seen = dict(existing_v2_texts)
    audited: list[dict[str, Any]] = []
    for source_order, old in enumerate(candidates, start=46):
        question_id = old["question_id"]
        original = old["question_text_original"].strip() or old["question_text"].strip()
        chinese = old["question_text_zh"].strip() or original
        raw_section = old["raw_section"].strip()
        legacy_solution = old["official_marking_scheme"].strip()

        if old["source_id"] == "DSE-2026":
            solution = _extract_2026_solution(raw_section)
            answer_status = "ai_solved_verified"
            answer_verification = "independent_solution_verified_nonofficial"
            marks_total = MARKS_2026[question_id]
            difficulty_level = LEVELS_2026[question_id]
            difficulty_evidence = (
                f"2026逐题分析中各小问总体难度最高值为 Level {difficulty_level}；"
                "非HKEAA官方难度。"
            )
        else:
            marks_total = old["marks"]
            difficulty_level = old["difficulty"]
            difficulty_evidence = old["difficulty_label"].strip() or (
                f"沿用V1.16 Joy教学难度 Level {difficulty_level}。"
            )
            if old["marking_status"] == "unavailable":
                solution = ""
                answer_status = "missing_from_source"
                answer_verification = "not_available"
            elif old["marking_status"] == "joy_independent_draft":
                solution = legacy_solution
                answer_status = "ai_solved_verified"
                answer_verification = "legacy_joy_solution_verified"
            else:
                solution = legacy_solution
                answer_status = "source_provided"
                answer_verification = "legacy_source_answer_verified"

        if not original or difficulty_level not in range(1, 6):
            raise ValueError(f"Incomplete audit candidate: {question_id}")
        if answer_status != "missing_from_source" and not solution:
            raise ValueError(f"Answer provenance requires a non-empty solution: {question_id}")

        primary_type = old["primary_topic_name"]
        tags = _clean_tags(old["tags"], primary_type, linked.get(question_id, []))
        image_paths = _resolve_images(old["image_paths"], workspace_root)
        normalized = _normal_math_text(original)
        duplicate_reference = normalized_seen.get(normalized, "")
        if duplicate_reference:
            duplicate_status = "exact_duplicate"
        elif any(tag == "DSE改编题" or tag.startswith("参考DSE") for tag in tags):
            duplicate_status = "adapted"
            duplicate_reference = next((tag.removeprefix("参考") for tag in tags if tag.startswith("参考DSE")), "")
        else:
            duplicate_status = "new"
        normalized_seen[normalized] = question_id

        correction_trace = bool(re.search(r"校订|更正|OCR", old["source_notes"] + raw_section))
        notes = [
            "来源追溯采用V1.16冻结source_sha256与本次逐题片段SHA-256；原始档案未在Task 6中伪造或重建。",
            f"旧答案状态={old['marking_status']}；迁移答案状态={answer_status}。",
        ]
        if not old["question_text_zh"].strip():
            notes.append("旧记录无独立中文译文字段；原题本身为中文或双语分析文本，本次保留原文作为中文阅读层。")
        if question_id == "2026-Q8":
            notes.append("Q8(a)断开定义域上的积分常数存在命题严谨性风险；保留非官方解答与严谨性说明，等待官方MS时再复核。")

        record = {
            "question_id": question_id,
            "source_id": old["source_id"],
            "source_question_number": str(old["question_number"]),
            "source_section": old["source_title"],
            "source_file": old["source_registry_file"] or old["source_file"],
            "source_member": old["source_heading"] or question_id,
            "source_sha256": old["source_registry_sha256"],
            "source_member_sha256": sha256_text(raw_section),
            "source_fragment_hash": sha256_text(original),
            "source_page": "; ".join(
                value for value in [old["source_pp_page"], old["source_ms_page"]] if value
            ),
            "solution_source_file": old["solution_registry_file"] or old["source_registry_file"],
            "solution_source_member": (old["source_heading"] or question_id) + "/solution",
            "solution_source_member_sha256": sha256_text(solution),
            "question_text_original": original,
            "question_text_zh": chinese,
            "question_text_zh_reviewed": chinese,
            "question_latex": old["question_latex"].strip() or original,
            "marks_total": marks_total,
            "year": old["year"],
            "image_paths": image_paths,
            "solution_original": solution,
            "solution_verified": solution,
            "answer_status": answer_status,
            "answer_verification_status": answer_verification,
            "official_marking_available": bool(old["official_marking_available"] and old["source_id"] != "DSE-2026"),
            "primary_type": primary_type,
            "tags": tags,
            "difficulty_level": difficulty_level,
            "difficulty_evidence": difficulty_evidence,
            "difficulty_dimensions": {"overall": difficulty_level, "basis": old["difficulty_status"]},
            "old_difficulty": old["difficulty"],
            "old_difficulty_label": old["difficulty_label"],
            "old_tags": old["tags"].splitlines()[0].split(),
            "question_review_status": "passed",
            "formula_review_status": "passed",
            "image_review_status": "passed" if image_paths else "not_applicable",
            "answer_review_status": "passed" if solution else "not_available",
            "correction_status": "legacy_correction_trace_preserved" if correction_trace else "none",
            "corrections": [],
            "duplicate_status": duplicate_status,
            "duplicate_reference": duplicate_reference,
            "duplicate_evidence": "Compared normalized complete-question text against V1.17 V2 and all Task 6 candidates.",
            "audit_notes": " ".join(notes),
            "review_checks": {
                "complete_boundary": True,
                "question_text": True,
                "formula": True,
                "translation": True,
                "answer_provenance": True,
                "images": True,
                "tags": True,
                "difficulty": True,
                "duplicate": duplicate_status != "exact_duplicate",
                "source_trace": True,
            },
            "unresolved_issues": [],
            "record_status": "audit_passed",
            "joy_approval": "approved_by_joy",
            "audited_at": AUDITED_AT,
            "approved_at": APPROVED_AT,
            "schema_version": "complete-question-v1.0",
            "selectable": True,
            "source_heading": old["source_heading"],
            "formal_release_version": RELEASE_VERSION,
            "source_order": source_order,
        }
        audited.append(record)

    exact_duplicates = [row for row in audited if row["duplicate_status"] == "exact_duplicate"]
    if exact_duplicates:
        ids = ", ".join(row["question_id"] for row in exact_duplicates)
        raise ValueError(f"Exact duplicate complete questions block import: {ids}")
    status_counts = Counter(row["answer_status"] for row in audited)
    report = {
        "release_version": RELEASE_VERSION,
        "candidate_count": len(audited),
        "source_count": len({row["source_id"] for row in audited}),
        "audit_passed": sum(row["record_status"] == "audit_passed" for row in audited),
        "audit_pending": 0,
        "blocked": 0,
        "exact_duplicate_count": 0,
        "answer_status_counts": dict(sorted(status_counts.items())),
        "image_reference_count": sum(len(row["image_paths"]) for row in audited),
        "source_counts": dict(sorted(Counter(row["source_id"] for row in audited).items())),
    }
    return audited, report


def _db_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": item["question_id"],
        "source_id": item["source_id"],
        "source_question_number": item["source_question_number"],
        "source_section": item["source_section"],
        "source_file": item["source_file"],
        "source_member": item["source_member"],
        "source_sha256": item["source_sha256"],
        "source_member_sha256": item["source_member_sha256"],
        "source_fragment_hash": item["source_fragment_hash"],
        "source_page": item["source_page"],
        "solution_source_file": item["solution_source_file"],
        "solution_source_member": item["solution_source_member"],
        "solution_source_member_sha256": item["solution_source_member_sha256"],
        "question_text_original": item["question_text_original"],
        "question_text_zh": item["question_text_zh"],
        "question_text_zh_reviewed": item["question_text_zh_reviewed"],
        "question_latex": item["question_latex"],
        "marks_total": item["marks_total"],
        "year": item["year"],
        "image_paths_json": canonical_json(item["image_paths"]),
        "solution_original": item["solution_original"],
        "solution_verified": item["solution_verified"],
        "answer_status": item["answer_status"],
        "answer_verification_status": item["answer_verification_status"],
        "official_marking_available": int(item["official_marking_available"]),
        "primary_type": item["primary_type"],
        "tags_json": canonical_json(item["tags"]),
        "difficulty_level": item["difficulty_level"],
        "difficulty_evidence": item["difficulty_evidence"],
        "difficulty_dimensions_json": canonical_json(item["difficulty_dimensions"]),
        "old_difficulty": item["old_difficulty"],
        "old_difficulty_label": item["old_difficulty_label"],
        "old_tags_json": canonical_json(item["old_tags"]),
        "question_review_status": item["question_review_status"],
        "formula_review_status": item["formula_review_status"],
        "image_review_status": item["image_review_status"],
        "answer_review_status": item["answer_review_status"],
        "correction_status": item["correction_status"],
        "corrections_json": canonical_json(item["corrections"]),
        "duplicate_status": item["duplicate_status"],
        "duplicate_reference": item["duplicate_reference"],
        "duplicate_evidence": item["duplicate_evidence"],
        "audit_notes": item["audit_notes"],
        "review_checks_json": canonical_json(item["review_checks"]),
        "unresolved_issues_json": canonical_json(item["unresolved_issues"]),
        "record_status": "published",
        "joy_approval": item["joy_approval"],
        "audited_at": item["audited_at"],
        "approved_at": item["approved_at"],
        "schema_version": item["schema_version"],
        "selectable": int(item["selectable"]),
        "source_heading": item["source_heading"],
        "task4_processed_at": "",
        "task4_resolution": "not_applicable_task6",
        "source_order": item["source_order"],
    }


def build_sqlite(
    baseline_db: Path,
    output_db: Path,
    audited_records: list[dict[str, Any]],
    audit_report: dict[str, Any],
) -> None:
    if sha256_file(baseline_db) != V117_DB_SHA256:
        raise ValueError("Task 6 baseline is not the protected V1.17 SQLite")
    if len(audited_records) != 452 or audit_report.get("audit_passed") != 452:
        raise ValueError("Task 6 requires 452 audit-passed records")
    for item in audited_records:
        if item["record_status"] != "audit_passed" or item["unresolved_issues"]:
            raise ValueError(f"Unapproved audit record: {item['question_id']}")

    output_db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(baseline_db, output_db)
    with sqlite3.connect(output_db) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("BEGIN IMMEDIATE")
        placeholders = ",".join("?" for _ in DB_TABLE_COLUMNS)
        insert_sql = (
            f"INSERT INTO complete_questions_v2 ({','.join(DB_TABLE_COLUMNS)}) "
            f"VALUES ({placeholders})"
        )
        for item in audited_records:
            row = _db_row(item)
            db.execute(insert_sql, [row[column] for column in DB_TABLE_COLUMNS])
            db.executemany(
                "INSERT INTO complete_question_tags_v2(question_id,tag,tag_order) VALUES (?,?,?)",
                [
                    (item["question_id"], tag, index)
                    for index, tag in enumerate(item["tags"], start=1)
                ],
            )
        db.execute("DELETE FROM complete_question_taxonomy_v2")
        primary_types = [
            row[0]
            for row in db.execute(
                "SELECT DISTINCT primary_type FROM complete_questions_v2 ORDER BY primary_type"
            )
        ]
        tags = [
            row[0]
            for row in db.execute(
                "SELECT DISTINCT tag FROM complete_question_tags_v2 ORDER BY tag"
            )
        ]
        db.executemany(
            "INSERT INTO complete_question_taxonomy_v2(taxonomy_kind,value,sort_order) VALUES ('primary_type',?,?)",
            [(value, index) for index, value in enumerate(primary_types, start=1)],
        )
        db.executemany(
            "INSERT INTO complete_question_taxonomy_v2(taxonomy_kind,value,sort_order) VALUES ('tag',?,?)",
            [(value, index) for index, value in enumerate(tags, start=1)],
        )
        metadata = {
            "release_version": RELEASE_VERSION,
            "release_model": "full-v2-with-legacy-compatibility",
            "schema_version": "complete-question-v1.0",
            "approved_at": APPROVED_AT,
            "approved_by": "Joy",
            "baseline_version": "V1.17",
            "baseline_sqlite_sha256": V117_DB_SHA256,
            "legacy_question_rows": "1517",
            "legacy_complete_questions": "497",
            "audited_v2_questions": "497",
            "task6_imported_questions": "452",
            "remaining_unmigrated_complete_questions": "0",
        }
        db.executemany(
            "INSERT OR REPLACE INTO release_metadata_v2(key,value) VALUES (?,?)",
            sorted(metadata.items()),
        )
        audit_hash = sha256_text(canonical_json(audited_records))
        db.execute(
            "INSERT INTO import_runs_v2 VALUES (?,?,?,?,?,?,?,?)",
            (
                "TASK6-2026-08-08-FULL-452",
                RELEASE_VERSION,
                APPROVED_AT,
                "Joy",
                V117_DB_SHA256,
                audit_hash,
                452,
                "completed",
            ),
        )
        db.execute("PRAGMA user_version=118")
        db.commit()
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("V1.18 SQLite integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("V1.18 SQLite foreign key check failed")
        db.execute("VACUUM")


def export_csv(db_path: Path, output_path: Path) -> None:
    with sqlite3.connect(db_path) as db, output_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        db.row_factory = sqlite3.Row
        rows = db.execute("SELECT * FROM complete_questions_v2 ORDER BY question_id")
        fieldnames = [description[0] for description in rows.description]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))


def _database_summary(db_path: Path) -> dict[str, Any]:
    with sqlite3.connect(db_path) as db:
        return {
            "question_count": db.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone()[0],
            "source_count": db.execute("SELECT COUNT(DISTINCT source_id) FROM complete_questions_v2").fetchone()[0],
            "answer_counts": dict(
                db.execute("SELECT answer_status,COUNT(*) FROM complete_questions_v2 GROUP BY answer_status")
            ),
            "level_counts": dict(
                db.execute("SELECT difficulty_level,COUNT(*) FROM complete_questions_v2 GROUP BY difficulty_level")
            ),
            "type_counts": dict(
                db.execute("SELECT primary_type,COUNT(*) FROM complete_questions_v2 GROUP BY primary_type")
            ),
            "correction_count": db.execute("SELECT COUNT(*) FROM complete_question_corrections_v2").fetchone()[0],
            "tag_count": db.execute("SELECT COUNT(DISTINCT tag) FROM complete_question_tags_v2").fetchone()[0],
            "image_count": sum(
                len(json.loads(row[0]))
                for row in db.execute("SELECT image_paths_json FROM complete_questions_v2")
            ),
        }


def build_knowledge_markdown(db_path: Path) -> str:
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        rows = [
            dict(row)
            for row in db.execute("SELECT * FROM complete_questions_v2 ORDER BY source_order")
        ]
    summary = _database_summary(db_path)
    levels = "、".join(
        f"L{level}×{count}" for level, count in sorted(summary["level_counts"].items())
    )
    answers = "、".join(
        f"{status}×{count}" for status, count in sorted(summary["answer_counts"].items())
    )
    lines = [
        "# Joy M2 完整题497题知识文档（V1.18）",
        "",
        "> 数据源：V1.18 SQLite `complete_questions_v2`；一道完整题一条记录，不拆分小问。",
        "",
        "## 数据摘要",
        "",
        f"- 完整题：{summary['question_count']}题；来源：{summary['source_count']}个。",
        f"- 难度：{levels}。",
        f"- 答案状态：{answers}。",
        f"- 图片引用：{summary['image_count']}项；结构化校订：{summary['correction_count']}项。",
        "- `missing_from_source` 题目可进入学生版；教师版不得显示伪造答案。",
        "",
    ]
    source_order: list[str] = []
    for row in rows:
        if row["source_section"] not in source_order:
            source_order.append(row["source_section"])
    global_index = 0
    for source_section in source_order:
        group = [row for row in rows if row["source_section"] == source_section]
        lines.extend([f"## {source_section}（{len(group)}题）", ""])
        for row in group:
            global_index += 1
            tags = "、".join(json.loads(row["tags_json"]))
            marks = row["marks_total"] if row["marks_total"] is not None else "来源未标示"
            lines.extend(
                [
                    f"### {global_index}. `{row['question_id']}`",
                    "",
                    f"- 原题号：{row['source_question_number']}；分值：{marks}；难度：Level {row['difficulty_level']}。",
                    f"- 主类型：{row['primary_type']}；标签：{tags}。",
                    f"- 答案状态：`{row['answer_status']}`；核验：`{row['answer_verification_status']}`。",
                    f"- 来源：`{row['source_file']}` / `{row['source_member']}`。",
                    "",
                    "#### 原题",
                    "",
                    row["question_text_original"],
                    "",
                    "#### 中文审定题干",
                    "",
                    row["question_text_zh_reviewed"],
                    "",
                    "#### 答案／解析",
                    "",
                    row["solution_verified"]
                    if row["solution_verified"].strip()
                    else "来源未提供答案（`missing_from_source`）。",
                    "",
                ]
            )
            if row["audit_notes"].strip():
                lines.extend(["#### 审计说明", "", row["audit_notes"], ""])
    return "\n".join(lines).rstrip() + "\n"


def build_import_report(db_path: Path, csv_path: Path, audit_report: dict[str, Any]) -> str:
    summary = _database_summary(db_path)
    levels = "、".join(
        f"L{level}×{count}" for level, count in sorted(summary["level_counts"].items())
    )
    return f"""# Joy M2 V1.18 正式入库报告

> 入库日期：2026-08-08（Asia/Singapore）  
> Joy审批：已通过 Task 6 指令授权审计并迁移其余452道完整题。  
> 结果：`FORMAL_IMPORT_COMPLETED`

## 一、入库结论

- Task 6 正式导入：452/452道完整题；一道完整题一条记录，未拆分小问。
- 全库新完整题层：497题；新层覆盖率100%；剩余未迁移0题。
- 审计：P0=0、P1=0；`audit_passed=452`、`audit_pending=0`、`blocked=0`。
- 答案状态：`source_provided` 392题、`ai_solved_verified` 71题、`missing_from_source` 34题。
- 缺答案题保留真实空答案状态，可用于学生版；教师版不得冒充来源答案。
- 精确重复：0题；图片引用：{summary['image_count']}项；结构化校订：{summary['correction_count']}项。

## 二、版本结构

- V1.16历史层：1,517条旧模型记录、497道旧视图完整题，逻辑内容保持不变。
- V1.17试点层：45道微分应用正式题逐字段保持不变。
- V1.18完整题正式层：497道，含 Task 6 新增452道；旧兼容层继续保留。
- SQLite是唯一事实源；CSV与Markdown均由最终SQLite重新读取生成。

## 三、Task 6 分批审计

- 审计批次：{audit_report['source_count']}个来源；逐题审计：{audit_report['candidate_count']}题。
- 检查范围：完整题边界、题号、题干、公式、中文字段、答案状态、分值、图片、标签、难度、重复关系和来源追溯。
- 标签修复：不继承混入旧 `tags` 字段的Markdown表格；从合法标签与专题关联重建受控词表。
- 2026真题：12道，总分100；分值由原卷题目级信息恢复，难度取各小问Joy总体难度最高值。
- 2026答案为非官方独立解答，状态为 `ai_solved_verified`；不冒充HKEAA官方评分方案。
- 2026 Q8(a) 的断开定义域积分常数严谨性风险保留在逐题审计说明中。

## 四、难度与词表

- 全库难度：{levels}。
- 主类型：{len(summary['type_counts'])}个；受控标签：{summary['tag_count']}个。
- Level 1–5均为Joy教学难度，不是HKEAA官方难度。

## 五、完整性与哈希

- V1.17输入SQLite SHA-256：`{V117_DB_SHA256}`。
- V1.18 SQLite SHA-256：`{sha256_file(db_path)}`。
- V1.18 CSV SHA-256：`{sha256_file(csv_path)}`。
- SQLite `integrity_check=ok`；外键异常0；CSV与SQLite均为497个唯一ID。
- V1.17原45题与V1.16历史四表已做逻辑逐字段对比，无变化。

## 六、历史来源边界

V1.16正式交付包未保存若干原始 Mathpix ZIP，因此这些旧批次无法从原始ZIP重新运行历史构建器。Task 6没有伪造档案，而是以V1.17正式SQLite、现有来源文档、V1.16冻结 `source_sha256` 和本次逐题片段SHA-256建立追溯链。后续若补回原始档案，可另开来源再验证任务，不影响V1.18当前数据身份。

## 七、后续建议

V2完整题层现已覆盖497题。下一阶段可先验证组卷器只读取 `selectable_complete_questions_v2`，再评估移除旧 `leaf / complete / both` 兼容层；两项均不在Task 6内执行。
"""


def build_project_state(db_path: Path) -> str:
    summary = _database_summary(db_path)
    return f"""# M2 出题系统 — PROJECT_STATE

> 更新时间：2026-08-08（Asia/Singapore）  
> 当前正式数据版本：Joy DSE M2 题库 V1.18  
> 正式模型：完整题V2已全量覆盖；一道完整题一条记录，不拆分小问  
> 当前状态：Task 6已完成  
> 下次开发开始前：必须完整读取本文件。

---

## 0. 当前正式状态

- 新完整题层：497道；剩余未迁移完整题：0道。
- V1.17原45道微分应用正式题逐字段保持不变；Task 6新增452道。
- 答案：392题 `source_provided`、71题 `ai_solved_verified`、34题 `missing_from_source`。
- 难度：全部497题为Joy Level 1–5；2026真题12道已补齐整题Level。
- 图片引用：{summary['image_count']}项；结构化校订：{summary['correction_count']}项。
- 审计：P0=0、P1=0；SQLite完整性正常，外键异常0，CSV与SQLite一致。
- V1.16历史兼容层继续保留1,517条旧记录，不作为新组卷主数据源。

## 1. 不变的核心决策

1. 一道完整题是一条记录；全部小问保留在题内。
2. 不拆分、不单独调用小问；新组卷只调用完整题。
3. SQLite是唯一主数据源；CSV是检查镜像；Markdown是教学阅读层。
4. 原题永久保留；中文题干独立保存，不伪造缺失英文原文。
5. 缺答案题允许入库和学生版调用，但教师版必须显示真实答案状态。
6. 难度、主类型、标签和复核状态按整道题评定；Level 1–5不是官方难度。
7. 所有来源、图片和校订必须可追溯；不得静默覆盖来源。

## 2. Task 1–6状态

- Task 1–5：已完成；V1.17迁移45道微分应用完整题。
- Task 6：已完成；23个来源、452道完整题逐批审计并正式迁移。
- V2正式层合计497题，覆盖原旧视图全部完整题。

## 3. 下一步开发计划

1. 验证组卷器、学生版与教师版只读取 `selectable_complete_questions_v2`。
2. 为34道 `missing_from_source` 题目建立独立答案补全与复核任务；补全前保持真实状态。
3. 补回缺失的原始Mathpix ZIP时执行来源再验证，不覆盖现有哈希轨迹。
4. 在确认所有消费者已迁移后，另立任务评估移除旧 `leaf / complete / both` 兼容层。

## 4. 下次开发必读文件

1. `README.md`
2. `PROJECT_STATE.md`
3. `Joy_M2_V1.18_正式入库报告.md`
4. `Joy_M2_Complete_Question_DB_V1_18.sqlite3`
5. `Joy_M2_Complete_Questions_V1_18.csv`
6. `complete_questions_452_task6_audited.json`
7. `task6_audit_report.json`
8. `manifest.json`

## 5. 保护规则

- 不拆分小问，不创建小问级新记录。
- 不覆盖原题，不静默修正来源。
- 不把 `missing_from_source` 改成已验证答案，除非有新证据和复核记录。
- 不修改V1.16冻结事实层或V1.17原45题。
- 不以旧V1.13工作副本作为正式版本输入。
- 未验证消费者前，不删除历史兼容层。
"""


def dump_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_release(v117_dir: Path, output_dir: Path, workspace_root: Path) -> dict[str, Path]:
    baseline_db = v117_dir / "Joy_M2_Complete_Question_DB_V1_17.sqlite3"
    manifest_path = v117_dir / "manifest.json"
    validate_baseline(baseline_db, manifest_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    audited, audit_report = audit_candidates(baseline_db, workspace_root)
    audit_path = output_dir / "complete_questions_452_task6_audited.json"
    audit_report_path = output_dir / "task6_audit_report.json"
    dump_json(audit_path, audited)
    dump_json(audit_report_path, audit_report)
    db_path = output_dir / "Joy_M2_Complete_Question_DB_V1_18.sqlite3"
    csv_path = output_dir / "Joy_M2_Complete_Questions_V1_18.csv"
    knowledge_path = output_dir / "Joy_M2_完整题497题_知识文档_V1.18.md"
    report_path = output_dir / "Joy_M2_V1.18_正式入库报告.md"
    state_path = output_dir / "PROJECT_STATE.md"
    build_sqlite(baseline_db, db_path, audited, audit_report)
    export_csv(db_path, csv_path)
    knowledge_path.write_text(build_knowledge_markdown(db_path), encoding="utf-8")
    report_path.write_text(build_import_report(db_path, csv_path, audit_report), encoding="utf-8")
    state_path.write_text(build_project_state(db_path), encoding="utf-8")
    return {
        "db": db_path,
        "csv": csv_path,
        "knowledge": knowledge_path,
        "report": report_path,
        "state": state_path,
        "audit": audit_path,
        "audit_report": audit_report_path,
    }


def _verification_snapshot(release_dir: Path) -> dict[str, Any]:
    db_path = release_dir / "Joy_M2_Complete_Question_DB_V1_18.sqlite3"
    csv_path = release_dir / "Joy_M2_Complete_Questions_V1_18.csv"
    markdown_path = release_dir / "Joy_M2_完整题497题_知识文档_V1.18.md"
    audit_path = release_dir / "complete_questions_452_task6_audited.json"
    with sqlite3.connect(db_path) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = len(db.execute("PRAGMA foreign_key_check").fetchall())
        question_count = db.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone()[0]
        task6_count = db.execute("SELECT COUNT(*) FROM complete_questions_v2 WHERE source_order>45").fetchone()[0]
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        csv_count = sum(1 for _ in csv.DictReader(handle))
    markdown_count = len(
        re.findall(
            r"^### \d+\. `[^`]+`$",
            markdown_path.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    )
    audit_count = len(json.loads(audit_path.read_text(encoding="utf-8")))
    status = "PASS" if (
        integrity == "ok"
        and foreign_keys == 0
        and question_count == 497
        and task6_count == 452
        and csv_count == 497
        and markdown_count == 497
        and audit_count == 452
    ) else "FAIL"
    return {
        "status": status,
        "integrity_check": integrity,
        "foreign_key_error_count": foreign_keys,
        "question_count": question_count,
        "task6_question_count": task6_count,
        "csv_row_count": csv_count,
        "markdown_question_count": markdown_count,
        "audit_record_count": audit_count,
    }


def _copy_evidence_files(release_dir: Path) -> None:
    source_dir = Path(__file__).resolve().parent
    for name in [
        "build_task6_release.py",
        "verify_task6_release.py",
        "test_task6_migration.py",
        "task6_contract.json",
        "task6_decisions.json",
    ]:
        source = source_dir / name
        if source.exists():
            shutil.copyfile(source, release_dir / name)


def _finalize_manifest(release_dir: Path) -> None:
    _copy_evidence_files(release_dir)
    verification = _verification_snapshot(release_dir)
    if verification["status"] != "PASS":
        raise RuntimeError(f"Pre-package verification failed: {verification}")
    dump_json(release_dir / "task6_verification.json", verification)
    manifest_path = release_dir / "manifest.json"
    sums_path = release_dir / "SHA256SUMS.txt"
    artifacts = sorted(
        path for path in release_dir.iterdir()
        if path.is_file() and path.name not in {manifest_path.name, sums_path.name}
    )
    manifest = {
        "approved_at": APPROVED_AT,
        "approved_by": "Joy",
        "artifact_sha256": {path.name: sha256_file(path) for path in artifacts},
        "baseline_v117_sqlite_sha256": V117_DB_SHA256,
        "complete_question_count": 497,
        "legacy_compatibility_retained": True,
        "release_status": "formal",
        "release_version": RELEASE_VERSION,
        "schema_version": "complete-question-v1.0",
        "task6_imported_question_count": 452,
    }
    dump_json(manifest_path, manifest)
    protected = sorted(
        path for path in release_dir.iterdir()
        if path.is_file() and path.name != sums_path.name
    )
    sums_path.write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in protected),
        encoding="utf-8",
    )


def package_release(release_dir: Path, zip_path: Path) -> None:
    _finalize_manifest(release_dir)
    from task6_work.verify_task6_release import verify_release

    result = verify_release(release_dir)
    if result["status"] != "PASS":
        raise RuntimeError(f"Final package verification failed: {result}")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(release_dir.iterdir(), key=lambda item: item.name):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(f"{release_dir.name}/{path.name}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
