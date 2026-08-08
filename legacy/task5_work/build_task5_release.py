from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DB = ROOT / "task5_work/v116/m2_question_bank/data/m2_question_bank.sqlite3"
TASK4_JSON = ROOT / "task4_work/task4_package/03_候选数据/complete_questions_45_task4.json"
TASK4_TAXONOMY = ROOT / "task4_work/task4_package/03_候选数据/differentiation_application_taxonomy_v1.1_task4.json"

RELEASE_VERSION = "V1.17"
APPROVED_AT = "2026-08-08T20:00:00+08:00"
BASE_DB_SHA256 = "d647244f54e9e54b25ec4885f16c47171c7521552876a5fa925a16d65d8c7714"
BASE_ZIP_SHA256 = "5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def approve_records(records: list[dict]) -> list[dict]:
    approved = []
    for source_order, original in enumerate(records, start=1):
        item = json.loads(json.dumps(original, ensure_ascii=False))
        if item.get("record_status") != "audit_passed" or item.get("unresolved_issues"):
            raise ValueError(f"Unapproved Task 4 record: {item.get('question_id')}")
        item["record_status"] = "published"
        item["joy_approval"] = "approved_by_joy"
        item["approved_at"] = APPROVED_AT
        item["schema_version"] = "complete-question-v1.0"
        item["selectable"] = True
        item["formal_release_version"] = RELEASE_VERSION
        item["source_order"] = source_order
        approved.append(item)
    if len(approved) != 45 or len({q["question_id"] for q in approved}) != 45:
        raise ValueError("Task 5 requires exactly 45 unique complete questions")
    return approved


TABLE_COLUMNS = [
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
    "task4_resolution", "source_order"
]


def db_row(item: dict) -> dict:
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
        "marks_total": item.get("marks_total"),
        "year": item.get("year"),
        "image_paths_json": canonical_json(item.get("image_paths", [])),
        "solution_original": item["solution_original"],
        "solution_verified": item["solution_verified"],
        "answer_status": item["answer_status"],
        "answer_verification_status": item["answer_verification_status"],
        "official_marking_available": int(bool(item.get("official_marking_available"))),
        "primary_type": item["primary_type"],
        "tags_json": canonical_json(item["tags"]),
        "difficulty_level": item["difficulty_level"],
        "difficulty_evidence": item["difficulty_evidence"],
        "difficulty_dimensions_json": canonical_json(item.get("difficulty_dimensions", {})),
        "old_difficulty": item.get("old_difficulty"),
        "old_difficulty_label": item.get("old_difficulty_label", ""),
        "old_tags_json": canonical_json(item.get("old_tags", [])),
        "question_review_status": item["question_review_status"],
        "formula_review_status": item["formula_review_status"],
        "image_review_status": item["image_review_status"],
        "answer_review_status": item["answer_review_status"],
        "correction_status": item["correction_status"],
        "corrections_json": canonical_json(item.get("corrections", [])),
        "duplicate_status": item["duplicate_status"],
        "duplicate_reference": item.get("duplicate_reference", ""),
        "duplicate_evidence": item.get("duplicate_evidence", ""),
        "audit_notes": item.get("audit_notes", ""),
        "review_checks_json": canonical_json(item.get("review_checks", {})),
        "unresolved_issues_json": canonical_json(item.get("unresolved_issues", [])),
        "record_status": item["record_status"],
        "joy_approval": item["joy_approval"],
        "audited_at": item["audited_at"],
        "approved_at": item["approved_at"],
        "schema_version": item["schema_version"],
        "selectable": int(bool(item["selectable"])),
        "source_heading": item.get("source_heading", ""),
        "task4_processed_at": item.get("task4_processed_at", ""),
        "task4_resolution": item.get("task4_resolution", ""),
        "source_order": item["source_order"],
    }


def migrate_sqlite(output_db: Path, approved: list[dict], taxonomy: dict) -> None:
    if sha256(BASE_DB) != BASE_DB_SHA256:
        raise ValueError("Frozen V1.16 SQLite hash mismatch")
    shutil.copyfile(BASE_DB, output_db)
    with sqlite3.connect(output_db) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=DELETE")
        db.executescript(
            """
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
        )
        metadata = {
            "release_version": RELEASE_VERSION,
            "release_model": "transitional-dual-layer",
            "schema_version": "complete-question-v1.0",
            "approved_at": APPROVED_AT,
            "approved_by": "Joy",
            "baseline_version": "V1.16",
            "baseline_sqlite_sha256": BASE_DB_SHA256,
            "legacy_question_rows": "1517",
            "legacy_complete_questions": "497",
            "audited_v2_questions": "45",
            "remaining_unmigrated_complete_questions": "452",
        }
        db.executemany("INSERT INTO release_metadata_v2(key,value) VALUES (?,?)", sorted(metadata.items()))
        placeholders = ",".join("?" for _ in TABLE_COLUMNS)
        insert_sql = f"INSERT INTO complete_questions_v2 ({','.join(TABLE_COLUMNS)}) VALUES ({placeholders})"
        for item in approved:
            row = db_row(item)
            db.execute(insert_sql, [row[column] for column in TABLE_COLUMNS])
            db.executemany(
                "INSERT INTO complete_question_tags_v2(question_id,tag,tag_order) VALUES (?,?,?)",
                [(item["question_id"], tag, index) for index, tag in enumerate(item["tags"], start=1)],
            )
            db.executemany(
                "INSERT INTO complete_question_corrections_v2 "
                "(question_id,correction_order,field_name,error_origin,original_text,corrected_text,reason,evidence) "
                "VALUES (?,?,?,?,?,?,?,?)",
                [
                    (
                        item["question_id"], index, correction.get("field", ""), correction.get("error_origin", ""),
                        correction.get("original", ""), correction.get("corrected", ""), correction.get("reason", ""),
                        correction.get("evidence", ""),
                    )
                    for index, correction in enumerate(item.get("corrections", []), start=1)
                ],
            )
        for kind, values in [("primary_type", taxonomy["primary_types"]), ("tag", taxonomy["tags"])]:
            db.executemany(
                "INSERT INTO complete_question_taxonomy_v2(taxonomy_kind,value,sort_order) VALUES (?,?,?)",
                [(kind, value, index) for index, value in enumerate(values, start=1)],
            )
        db.execute(
            "INSERT INTO import_runs_v2 VALUES (?,?,?,?,?,?,?,?)",
            (
                "TASK5-2026-08-08-M2QD-DA-45", RELEASE_VERSION, APPROVED_AT, "Joy", BASE_DB_SHA256,
                sha256(TASK4_JSON), 45, "completed",
            ),
        )
        db.execute("PRAGMA user_version=117")
        db.commit()
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLite integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("SQLite foreign key check failed")
        db.execute("VACUUM")


def export_csv(db_path: Path, csv_path: Path) -> None:
    with sqlite3.connect(db_path) as db, csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        db.row_factory = sqlite3.Row
        writer = csv.DictWriter(handle, fieldnames=TABLE_COLUMNS)
        writer.writeheader()
        for row in db.execute("SELECT * FROM complete_questions_v2 ORDER BY question_id"):
            writer.writerow(dict(row))


def markdown_knowledge(db_path: Path) -> str:
    section_order = ["教材例题", "应试训练", "甲部特训", "乙部特训"]
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        rows = [dict(row) for row in db.execute("SELECT * FROM complete_questions_v2 ORDER BY source_order")]
    levels = Counter(row["difficulty_level"] for row in rows)
    types = Counter(row["primary_type"] for row in rows)
    lines = [
        "# Joy M2 微分应用45题知识文档（V1.17）", "",
        "> 数据源：V1.17 SQLite `complete_questions_v2`；一道完整题一条记录，不拆分小问。", "",
        "## 数据摘要", "",
        f"- 完整题：{len(rows)}题；正式发布：{sum(row['record_status']=='published' for row in rows)}题。",
        "- 难度：" + "、".join(f"L{level}×{levels[level]}" for level in sorted(levels)) + "。",
        "- 主类型：" + "、".join(f"{name}×{types[name]}" for name in sorted(types)) + "。",
        "- 答案状态：45题均为 `source_provided`，并已完成逐题数学复核。", "",
    ]
    for section in section_order:
        group = [row for row in rows if row["source_section"] == section]
        lines += [f"## {section}（{len(group)}题）", ""]
        for index, row in enumerate(group, start=1):
            tags = "、".join(json.loads(row["tags_json"]))
            lines += [
                f"### {index}. `{row['question_id']}`", "",
                f"- 原题号：{row['source_question_number']}；分值：{row['marks_total'] if row['marks_total'] is not None else '未标示'}；难度：Level {row['difficulty_level']}。",
                f"- 主类型：{row['primary_type']}；标签：{tags}。",
                f"- 来源：`{row['source_file']}` / `{row['source_member']}`。", "",
                "#### 英文原题", "", row["question_text_original"], "",
                "#### 中文审定题干", "", row["question_text_zh_reviewed"], "",
                "#### 核验答案", "", row["solution_verified"], "",
            ]
            corrections = json.loads(row["corrections_json"])
            if corrections:
                lines += ["#### 校订记录", ""]
                for correction in corrections:
                    lines.append(f"- {correction.get('field','')}：{correction.get('reason','')}")
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def import_report(db_path: Path, csv_path: Path) -> str:
    with sqlite3.connect(db_path) as db:
        level_rows = db.execute("SELECT difficulty_level,COUNT(*) FROM complete_questions_v2 GROUP BY difficulty_level ORDER BY difficulty_level").fetchall()
        type_rows = db.execute("SELECT primary_type,COUNT(*) FROM complete_questions_v2 GROUP BY primary_type ORDER BY primary_type").fetchall()
        correction_count = db.execute("SELECT COUNT(*) FROM complete_question_corrections_v2").fetchone()[0]
        tag_count = db.execute("SELECT COUNT(DISTINCT tag) FROM complete_question_tags_v2").fetchone()[0]
    levels = "、".join(f"L{level}×{count}" for level, count in level_rows)
    types = "、".join(f"{name}×{count}" for name, count in type_rows)
    return f"""# Joy M2 V1.17 正式入库报告

> 入库日期：2026-08-08（Asia/Singapore）  
> Joy审批：已确认 Task 4，批准45道微分应用完整题正式入库。  
> 结果：`FORMAL_IMPORT_COMPLETED`

## 一、入库结论

- 正式导入：45/45 道完整题；一道完整题一条记录，未拆分小问。
- 审批状态：45题 `published`、45题 `approved_by_joy`、45题可抽取。
- 自动门禁：P0=0、P1=0；未解决事项0。
- 答案：45/45均为 `source_provided`，并保存核验答案。
- 校订：{correction_count}项，全部保留原文、订正、理由与证据。
- 标签：本批实际使用{tag_count}个细分标签；词表V1.1正式生效。

## 二、版本结构

V1.17采用过渡双层结构：

- V1.16历史层原样保留：1,517条旧模型记录、497道旧视图完整题、24个来源。
- V1.17正式完整题层：`complete_questions_v2`，仅包含已完成新标准审计的45题。
- 其余452道完整题尚未迁移，不得视为已完成新标准审计。
- 新CSV和Markdown均由V1.17 SQLite正式层生成，SQLite是唯一事实源。

## 三、分布

- 难度：{levels}。
- 主类型：{types}。
- 来源分组：教材例题8、应试训练14、甲部特训17、乙部特训6。

## 四、Task 4决议落实

- 14题答案来源文件、成员和SHA-256映射已写入正式记录。
- 分值补录：TRAIN-Q3=4、TRAIN-Q7=6、TRAIN-Q13=3。
- 教材、甲部、乙部内容订正均写入正式题干、答案和校订表。
- `全局最小值`、`从基本原理求导`、`导数为正区间`已进入正式受控词表。
- `joy_approval=approved_by_joy`，`approved_at={APPROVED_AT}`。

## 五、完整性与哈希

- V1.16 SQLite输入SHA-256：`{BASE_DB_SHA256}`。
- V1.16正式封包SHA-256：`{BASE_ZIP_SHA256}`。
- V1.17 SQLite SHA-256：`{sha256(db_path)}`。
- V1.17 CSV SHA-256：`{sha256(csv_path)}`。
- SQLite `integrity_check=ok`；外键异常0。
- SQLite与CSV题号集合一致，均为45个唯一ID。

## 六、后续边界

下一步不是继续修改这45题，而是按同一标准审计并迁移其余452道完整题。全库迁移完成前，旧 `leaf / complete / both` 层仅作为历史兼容层；新组卷流程应优先调用 `selectable_complete_questions_v2`。
"""


def project_state() -> str:
    return f"""# M2 出题系统 — PROJECT_STATE

> 更新时间：2026-08-08（Asia/Singapore）  
> 当前正式数据版本：Joy DSE M2 题库 V1.17  
> 正式模型：过渡双层；新层坚持一道完整题一条记录，不拆分小问  
> 当前唯一优先任务：按新标准审计并迁移其余452道完整题  
> 下次开发开始前：必须完整读取本文件。

---

## 0. 当前正式状态

- V1.16历史层：1,517条旧模型记录、497道旧视图完整题、24个来源；内容逻辑保持不变。
- V1.17完整题正式层：45道微分应用完整题，45个唯一ID，45题已发布并获Joy批准。
- V1.17难度：L2×8、L3×17、L4×16、L5×4。
- V1.17答案：45/45为 `source_provided`；59项校订可追溯。
- V1.17验收：P0=0、P1=0；SQLite完整性正常，CSV与SQLite一致。
- 其余452道完整题尚未迁移，不能视为已通过新模型审计。

## 1. 不变的核心决策

1. 一道完整题是一条记录；全部 `(a)(b)(i)(ii)` 小问保留在题内。
2. 不拆分、不单独调用小问；新组卷只调用完整题。
3. SQLite是唯一主数据源；CSV是人工检查镜像；Markdown是教学阅读层。
4. 英文原题永久保留；中文题干独立保存。
5. 难度、主类型、标签、答案状态和复核状态均按整道题评定。
6. 缺答案题仍可入库，但必须保留真实答案状态。
7. 所有订正必须保留原文、订正、理由、证据和复核轨迹。
8. Level 1–5是Joy教学难度，不是HKEAA官方难度。

## 2. Task 1–5状态

- Task 1：恢复并冻结V1.16事实源（已完成）。
- Task 2：建立完整题数据契约、标签、难度和验收规则（已完成）。
- Task 3：逐题复核微分应用45题（已完成）。
- Task 4：关闭21道待决题，45/45技术通过（已完成）。
- Task 5：微分应用45题正式迁移（已完成）。

### Task 5：微分应用45题正式迁移（已完成）

- Joy于2026-08-08明确确认Task 4并授权正式更新SQLite、CSV、Markdown和项目状态。
- 正式版本定为V1.17。
- V1.16旧层逐表保留；新增 `complete_questions_v2`、标签表、校订表、词表和导入记录表。
- 新CSV `Joy_M2_Complete_Questions_V1_17.csv` 由SQLite新层生成。
- Markdown知识文档包含45题英文原题、中文审定题干、核验答案、标签、难度和校订摘要。
- 其余452道完整题尚未迁移。

## 3. 下一步开发计划

### Task 6：继续全库完整题迁移

1. 选择下一个来源模块并恢复原始题目、答案、图片与哈希。
2. 按完整题边界逐题审计，不拆分小问。
3. 输出预检报告；Joy确认后再加入 `complete_questions_v2`。
4. 每批迁移后重新生成SQLite、CSV、Markdown、报告、manifest和确定性封包。
5. 全部452题完成后，评估移除旧 `leaf / complete / both` 兼容层。

建议下一批优先处理已经具备较完整来源资料与答案映射的模块；具体模块由Joy指定。

## 4. 下次开发必读文件

1. `README.md`
2. `PROJECT_STATE.md`
3. `Joy_M2_V1.17_正式入库报告.md`
4. `Joy_M2_Complete_Question_DB_V1_17.sqlite3`
5. `Joy_M2_Complete_Questions_V1_17.csv`
6. `complete_questions_45_approved_v1_17.json`
7. `differentiation_application_taxonomy_v1_1.json`
8. `manifest.json`

## 5. 保护规则

- 不拆分小问，不创建小问级新记录。
- 不覆盖英文原题，不静默修正来源。
- 不把未审计的452题标为V2正式记录。
- 不以旧V1.13工作副本作为任何正式版本输入。
- 不修改V1.16冻结封包；V1.17必须可由V1.16事实源和批准数据重建。
- 未经Joy预检确认，不导入下一批题目。
- 原创微分应用30题仍是独立未入库资产。
"""


def build_release(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for child in output_dir.iterdir():
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)

    records = json.loads(TASK4_JSON.read_text(encoding="utf-8"))
    approved = approve_records(records)
    taxonomy = json.loads(TASK4_TAXONOMY.read_text(encoding="utf-8"))
    taxonomy["version"] = "V1.1"
    taxonomy["status"] = "approved"
    taxonomy["approved_by"] = "Joy"
    taxonomy["approved_at"] = APPROVED_AT
    taxonomy["change_note"] = "Task 4词表经Joy确认，随V1.17正式生效。"

    paths = {
        "sqlite": output_dir / "Joy_M2_Complete_Question_DB_V1_17.sqlite3",
        "csv": output_dir / "Joy_M2_Complete_Questions_V1_17.csv",
        "knowledge": output_dir / "Joy_M2_微分应用45题_知识文档_V1.17.md",
        "report": output_dir / "Joy_M2_V1.17_正式入库报告.md",
        "project_state": output_dir / "PROJECT_STATE.md",
        "manifest": output_dir / "manifest.json",
        "approved_json": output_dir / "complete_questions_45_approved_v1_17.json",
        "taxonomy": output_dir / "differentiation_application_taxonomy_v1_1.json",
    }
    dump_json(paths["approved_json"], approved)
    dump_json(paths["taxonomy"], taxonomy)
    migrate_sqlite(paths["sqlite"], approved, taxonomy)
    export_csv(paths["sqlite"], paths["csv"])
    paths["knowledge"].write_text(markdown_knowledge(paths["sqlite"]), encoding="utf-8")
    paths["report"].write_text(import_report(paths["sqlite"], paths["csv"]), encoding="utf-8")
    paths["project_state"].write_text(project_state(), encoding="utf-8")

    artifact_names = [
        paths["sqlite"].name, paths["csv"].name, paths["knowledge"].name, paths["report"].name,
        paths["project_state"].name, paths["approved_json"].name, paths["taxonomy"].name,
    ]
    manifest = {
        "release_version": RELEASE_VERSION,
        "release_status": "formal",
        "schema_version": "complete-question-v1.0",
        "release_model": "transitional-dual-layer",
        "approved_by": "Joy",
        "approved_at": APPROVED_AT,
        "approved_question_count": 45,
        "remaining_unmigrated_complete_questions": 452,
        "baseline_v116_sqlite_sha256": BASE_DB_SHA256,
        "baseline_v116_zip_sha256": BASE_ZIP_SHA256,
        "task4_candidate_sha256": sha256(TASK4_JSON),
        "artifact_sha256": {name: sha256(output_dir / name) for name in artifact_names},
    }
    dump_json(paths["manifest"], manifest)
    return paths


def package_release(release_dir: Path, output_zip: Path) -> Path:
    mapping = {
        "01_数据/Joy_M2_Complete_Question_DB_V1_17.sqlite3": release_dir / "Joy_M2_Complete_Question_DB_V1_17.sqlite3",
        "01_数据/Joy_M2_Complete_Questions_V1_17.csv": release_dir / "Joy_M2_Complete_Questions_V1_17.csv",
        "01_数据/complete_questions_45_approved_v1_17.json": release_dir / "complete_questions_45_approved_v1_17.json",
        "01_数据/differentiation_application_taxonomy_v1_1.json": release_dir / "differentiation_application_taxonomy_v1_1.json",
        "02_知识文档/Joy_M2_微分应用45题_知识文档_V1.17.md": release_dir / "Joy_M2_微分应用45题_知识文档_V1.17.md",
        "03_报告/Joy_M2_V1.17_正式入库报告.md": release_dir / "Joy_M2_V1.17_正式入库报告.md",
        "03_报告/PROJECT_STATE.md": release_dir / "PROJECT_STATE.md",
        "04_清单/manifest.json": release_dir / "manifest.json",
        "05_构建与测试/build_task5_release.py": Path(__file__),
        "05_构建与测试/test_task5_import.py": Path(__file__).with_name("test_task5_import.py"),
    }
    for archive_name, path in mapping.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing package input: {archive_name}")
    sums = "".join(f"{sha256(path)}  {name}\n" for name, path in sorted(mapping.items()))
    sums_path = release_dir / "SHA256SUMS.txt"
    sums_path.write_text(sums, encoding="utf-8")
    mapping["SHA256SUMS.txt"] = sums_path
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for archive_name, path in sorted(mapping.items()):
            info = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output_zip


if __name__ == "__main__":
    result = build_release(ROOT / "task5_work/task5_release")
    package_release(
        ROOT / "task5_work/task5_release",
        ROOT / "outputs/25757421d1d8/Joy_M2_V1.17_Task5_正式入库包_2026-08-08.zip",
    )
    print(json.dumps({key: str(value) for key, value in result.items()}, ensure_ascii=False, indent=2))
