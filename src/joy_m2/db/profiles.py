"""Deterministic SQLite profiles for the maintained database boundary."""

from __future__ import annotations

from dataclasses import asdict
import json

from ..models import AuditedRecord, V117ReleaseRecord


DB_TABLE_COLUMNS = (
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
)

V117_PRIMARY_TYPES = (
    "切线与法线",
    "极值与曲线性质",
    "最值与最优化",
    "变率",
    "综合微分应用",
)

V117_TAGS = (
    "已知切点求切线", "过指定点的切线", "与指定直线平行的切线", "切点未知",
    "已知切点求法线", "切点未知求法线", "驻点", "极大点", "极小点",
    "一阶导数判别法", "二阶导数判别法", "拐点", "凹凸性", "渐近线", "曲线作图",
    "区间最值", "端点比较", "几何最优化", "实际情境最优化", "相关变化率", "运动学",
    "几何量变化", "体积变化", "面积变化", "链式法则建模", "隐函数求导", "参数方程",
    "建立变量关系", "综合题目", "全局最小值", "从基本原理求导", "导数为正区间",
)

V117_SCHEMA_SQL = """
BEGIN IMMEDIATE;
CREATE TABLE release_metadata_v2 (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE complete_questions_v2 (
    question_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_file TEXT NOT NULL,
    source_member TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    source_member_sha256 TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL,
    source_page TEXT NOT NULL,
    solution_source_file TEXT NOT NULL,
    solution_source_member TEXT NOT NULL,
    solution_source_member_sha256 TEXT NOT NULL,
    question_text_original TEXT NOT NULL,
    question_text_zh TEXT NOT NULL,
    question_text_zh_reviewed TEXT NOT NULL,
    question_latex TEXT NOT NULL,
    marks_total INTEGER,
    year INTEGER,
    image_paths_json TEXT NOT NULL,
    solution_original TEXT NOT NULL,
    solution_verified TEXT NOT NULL,
    answer_status TEXT NOT NULL,
    answer_verification_status TEXT NOT NULL,
    official_marking_available INTEGER NOT NULL CHECK(official_marking_available IN (0,1)),
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    difficulty_level INTEGER NOT NULL CHECK(difficulty_level BETWEEN 1 AND 5),
    difficulty_evidence TEXT NOT NULL,
    difficulty_dimensions_json TEXT NOT NULL,
    old_difficulty INTEGER,
    old_difficulty_label TEXT NOT NULL,
    old_tags_json TEXT NOT NULL,
    question_review_status TEXT NOT NULL,
    formula_review_status TEXT NOT NULL,
    image_review_status TEXT NOT NULL,
    answer_review_status TEXT NOT NULL,
    correction_status TEXT NOT NULL,
    corrections_json TEXT NOT NULL,
    duplicate_status TEXT NOT NULL CHECK(duplicate_status IN ('new','adapted','historical_reference','exact_duplicate')),
    duplicate_reference TEXT NOT NULL,
    duplicate_evidence TEXT NOT NULL,
    audit_notes TEXT NOT NULL,
    review_checks_json TEXT NOT NULL,
    unresolved_issues_json TEXT NOT NULL CHECK(unresolved_issues_json='[]'),
    record_status TEXT NOT NULL CHECK(record_status='published'),
    joy_approval TEXT NOT NULL CHECK(joy_approval='approved_by_joy'),
    audited_at TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    schema_version TEXT NOT NULL CHECK(schema_version='complete-question-v1.0'),
    selectable INTEGER NOT NULL CHECK(selectable IN (0,1)),
    source_heading TEXT NOT NULL,
    task4_processed_at TEXT NOT NULL,
    task4_resolution TEXT NOT NULL,
    source_order INTEGER NOT NULL UNIQUE
);
CREATE TABLE complete_question_tags_v2 (
    question_id TEXT NOT NULL REFERENCES complete_questions_v2(question_id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    tag_order INTEGER NOT NULL,
    PRIMARY KEY(question_id, tag)
);
CREATE TABLE complete_question_corrections_v2 (
    question_id TEXT NOT NULL REFERENCES complete_questions_v2(question_id) ON DELETE CASCADE,
    correction_order INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    error_origin TEXT NOT NULL,
    original_text TEXT NOT NULL,
    corrected_text TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence TEXT NOT NULL,
    PRIMARY KEY(question_id, correction_order)
);
CREATE TABLE complete_question_taxonomy_v2 (
    taxonomy_kind TEXT NOT NULL CHECK(taxonomy_kind IN ('primary_type','tag')),
    value TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    PRIMARY KEY(taxonomy_kind, value)
);
CREATE TABLE import_runs_v2 (
    import_id TEXT PRIMARY KEY,
    release_version TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    baseline_sqlite_sha256 TEXT NOT NULL,
    task4_candidate_sha256 TEXT NOT NULL,
    imported_question_count INTEGER NOT NULL,
    status TEXT NOT NULL
);
CREATE VIEW selectable_complete_questions_v2 AS
    SELECT * FROM complete_questions_v2
    WHERE record_status='published' AND joy_approval='approved_by_joy' AND selectable=1;
CREATE INDEX idx_complete_questions_v2_type ON complete_questions_v2(primary_type);
CREATE INDEX idx_complete_questions_v2_level ON complete_questions_v2(difficulty_level);
CREATE INDEX idx_complete_questions_v2_source ON complete_questions_v2(source_id, source_section);
COMMIT;
"""
V117_SCHEMA_SQL = "\n".join(
    f"            {line}" for line in V117_SCHEMA_SQL.splitlines()
)

# SQLite records its library version in bytes 96:100. The frozen releases were
# produced by 3.50.4, so normalize this non-semantic header field after VACUUM.
FROZEN_SQLITE_HEADER_VERSION = 3_050_004


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _question_values(record: AuditedRecord) -> dict[str, object]:
    question = record.question
    return {
        "question_id": question.question_id,
        "source_id": question.source_id,
        "source_question_number": question.source_question_number,
        "source_section": question.source_section,
        "source_file": question.source_file,
        "source_member": question.source_member,
        "source_sha256": question.source_sha256,
        "source_member_sha256": question.source_member_sha256,
        "source_fragment_hash": question.source_fragment_hash,
        "source_page": question.source_page,
        "solution_source_file": question.solution_source_file,
        "solution_source_member": question.solution_source_member,
        "solution_source_member_sha256": question.solution_source_member_sha256,
        "question_text_original": question.question_text_original,
        "question_text_zh": question.question_text_zh,
        "question_text_zh_reviewed": question.question_text_zh_reviewed,
        "question_latex": question.question_latex,
        "marks_total": question.marks_total,
        "year": question.year,
        "solution_original": question.solution_original,
        "solution_verified": question.solution_verified,
        "answer_status": question.answer_status,
        "answer_verification_status": question.answer_verification_status,
        "official_marking_available": question.official_marking_available,
        "primary_type": question.primary_type,
        "tags": list(question.tags),
        "difficulty_level": question.difficulty_level,
        "difficulty_evidence": question.difficulty_evidence,
        "difficulty_dimensions": dict(question.difficulty_dimensions),
        "old_difficulty": question.old_difficulty,
        "old_difficulty_label": question.old_difficulty_label,
        "old_tags": list(question.old_tags),
        "question_review_status": question.question_review_status,
        "formula_review_status": question.formula_review_status,
        "image_review_status": question.image_review_status,
        "answer_review_status": question.answer_review_status,
        "correction_status": question.correction_status,
        "corrections": [asdict(correction) for correction in question.corrections],
        "duplicate_status": question.duplicate_status,
        "duplicate_reference": question.duplicate_reference,
        "duplicate_evidence": question.duplicate_evidence,
        "audit_notes": question.audit_notes,
        "review_checks": dict(question.review_checks),
        "unresolved_issues": list(question.unresolved_issues),
        "audited_at": question.audited_at,
        "source_heading": question.source_heading,
    }


def _database_row(values: dict[str, object]) -> dict[str, object]:
    row = dict(values)
    for source, target in (
        ("image_paths", "image_paths_json"),
        ("tags", "tags_json"),
        ("difficulty_dimensions", "difficulty_dimensions_json"),
        ("old_tags", "old_tags_json"),
        ("corrections", "corrections_json"),
        ("review_checks", "review_checks_json"),
        ("unresolved_issues", "unresolved_issues_json"),
    ):
        row[target] = canonical_json(row.pop(source))
    row["official_marking_available"] = int(row["official_marking_available"])
    row["selectable"] = int(row["selectable"])
    return row


def v118_external_record(record: AuditedRecord) -> dict[str, object]:
    question = record.question
    publication = question.publication_evidence
    compatibility = record.release_compatibility
    assert compatibility is not None
    return _question_values(record) | {
        "image_paths": [image.path for image in question.image_paths],
        "record_status": publication.record_status,
        "joy_approval": publication.joy_approval,
        "approved_at": publication.approved_at,
        "schema_version": question.schema_version,
        "formal_release_version": compatibility.formal_release_version,
        "selectable": compatibility.selectable,
        "source_order": compatibility.source_order,
    }


def v118_database_row(record: AuditedRecord) -> dict[str, object]:
    values = v118_external_record(record)
    values["record_status"] = "published"
    values["task4_processed_at"] = ""
    values["task4_resolution"] = "not_applicable_task6"
    values.pop("formal_release_version")
    return _database_row(values)


def v117_database_row(record: V117ReleaseRecord) -> dict[str, object]:
    audited = record.audited_record
    question = audited.question
    task4 = audited.task4_compatibility
    assert task4 is not None
    values = _question_values(audited) | {
        "image_paths": [asdict(image) for image in question.image_paths],
        "record_status": record.publication_evidence.record_status,
        "joy_approval": record.publication_evidence.joy_approval,
        "approved_at": record.publication_evidence.approved_at,
        "schema_version": record.schema_version,
        "selectable": record.release_compatibility.selectable,
        "source_order": record.release_compatibility.source_order,
        "task4_processed_at": (
            task4.task4_processed_at if task4.task4_processed_at_present else ""
        ),
        "task4_resolution": (
            task4.task4_resolution if task4.task4_resolution_present else ""
        ),
    }
    return _database_row(values)
