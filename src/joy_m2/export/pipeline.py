"""Maintained deterministic database and audit-evidence exports."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile

from ..audit.profiles import serialize_v117_record, serialize_v118_record
from ..db.profiles import V117_PRIMARY_TYPES, V117_TAGS
from ..errors import InputMissingError, OutputConflictError, PipelineError
from ..models import (
    ArtifactRef,
    AuditedBatch,
    DerivedArtifacts,
    ExportRequest,
    ExportVerificationRequest,
    VerificationCheck,
    VerificationReport,
    V117ReleaseBatch,
)
from .formats import csv_bytes, evidence_json_bytes, text_bytes


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _check(name: str, passed: bool, detail: str) -> VerificationCheck:
    return VerificationCheck(name=name, passed=passed, detail=detail)


def _require_database(request: ExportRequest) -> Path:
    reference = request.database.database
    path = reference.path
    if reference.kind != "sqlite":
        raise PipelineError("export database ArtifactRef must have kind 'sqlite'")
    if not path.is_file():
        raise InputMissingError(f"export database does not exist: {path}")
    if path.stat().st_size != reference.size_bytes or _sha256_file(path) != reference.sha256:
        raise PipelineError("export database identity does not match its ArtifactRef")
    if request.database.verification_report.status != "PASS":
        raise PipelineError("export requires a verified database artifact")
    return path


def _batch_audited_records(request: ExportRequest) -> tuple:
    profile = request.contract.profile
    if profile == "V1.18" and type(request.record_batch) is AuditedBatch:
        records = request.record_batch.records
    elif profile == "V1.17" and type(request.record_batch) is V117ReleaseBatch:
        records = tuple(record.audited_record for record in request.record_batch.records)
    else:
        raise PipelineError("export profile received the wrong record batch type")
    if records != request.audit_result.records:
        raise PipelineError("record_batch must match audit_result records and order")
    request.audit_result.require_passed()
    if request.audit_result.report.release_version != profile:
        raise PipelineError("audit report release version must match export profile")
    return records


def _database_rows(path: Path, order_by: str) -> tuple[tuple[str, ...], list[dict]]:
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
            database.row_factory = sqlite3.Row
            cursor = database.execute(
                f"SELECT * FROM complete_questions_v2 ORDER BY {order_by}"
            )
            fieldnames = tuple(column[0] for column in cursor.description)
            return fieldnames, [dict(row) for row in cursor]
    except sqlite3.Error as error:
        raise PipelineError("export database cannot be read") from error


def _database_summary(path: Path) -> dict[str, object]:
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
            return {
                "question_count": database.execute(
                    "SELECT COUNT(*) FROM complete_questions_v2"
                ).fetchone()[0],
                "source_count": database.execute(
                    "SELECT COUNT(DISTINCT source_id) FROM complete_questions_v2"
                ).fetchone()[0],
                "answer_counts": dict(
                    database.execute(
                        "SELECT answer_status,COUNT(*) FROM complete_questions_v2 "
                        "GROUP BY answer_status"
                    )
                ),
                "level_counts": dict(
                    database.execute(
                        "SELECT difficulty_level,COUNT(*) FROM complete_questions_v2 "
                        "GROUP BY difficulty_level"
                    )
                ),
                "type_counts": dict(
                    database.execute(
                        "SELECT primary_type,COUNT(*) FROM complete_questions_v2 "
                        "GROUP BY primary_type"
                    )
                ),
                "correction_count": database.execute(
                    "SELECT COUNT(*) FROM complete_question_corrections_v2"
                ).fetchone()[0],
                "tag_count": database.execute(
                    "SELECT COUNT(DISTINCT tag) FROM complete_question_tags_v2"
                ).fetchone()[0],
                "image_count": sum(
                    len(json.loads(row[0]))
                    for row in database.execute(
                        "SELECT image_paths_json FROM complete_questions_v2"
                    )
                ),
            }
    except (sqlite3.Error, json.JSONDecodeError) as error:
        raise PipelineError("export database summary cannot be produced") from error


def _audit_report_value(request: ExportRequest) -> dict[str, object]:
    value = asdict(request.audit_result.report)
    value.pop("status")
    value["answer_status_counts"] = dict(request.audit_result.report.answer_status_counts)
    value["source_counts"] = dict(request.audit_result.report.source_counts)
    return value


def _audit_records_value(request: ExportRequest) -> list[dict]:
    if request.contract.profile == "V1.18":
        return [serialize_v118_record(record) for record in request.audit_result.records]
    if type(request.record_batch) is not V117ReleaseBatch:
        raise PipelineError("V1.17 audit evidence requires a V117ReleaseBatch")
    values: list[dict] = []
    for release_record in request.record_batch.records:
        value = serialize_v117_record(release_record.audited_record)
        value.update(
            record_status=release_record.publication_evidence.record_status,
            joy_approval=release_record.publication_evidence.joy_approval,
            approved_at=release_record.publication_evidence.approved_at,
            schema_version=release_record.schema_version,
            formal_release_version=(
                release_record.release_compatibility.formal_release_version
            ),
            selectable=release_record.release_compatibility.selectable,
            source_order=release_record.release_compatibility.source_order,
        )
        values.append(value)
    return values


def _v117_taxonomy_value() -> dict[str, object]:
    return {
        "approved_at": "2026-08-08T20:00:00+08:00",
        "approved_by": "Joy",
        "change_note": "Task 4词表经Joy确认，随V1.17正式生效。",
        "primary_types": list(V117_PRIMARY_TYPES),
        "status": "approved",
        "tagging_rule": "只标题目明确要求的能力。",
        "tags": list(V117_TAGS),
        "updated_at": "2026-08-08T20:00:00+08:00",
        "version": "V1.1",
    }


def _v117_knowledge(rows: list[dict]) -> str:
    section_order = ["教材例题", "应试训练", "甲部特训", "乙部特训"]
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


def _v118_knowledge(rows: list[dict], summary: dict[str, object]) -> str:
    levels = "、".join(
        f"L{level}×{count}"
        for level, count in sorted(summary["level_counts"].items())
    )
    answers = "、".join(
        f"{status}×{count}"
        for status, count in sorted(summary["answer_counts"].items())
    )
    lines = [
        "# Joy M2 完整题497题知识文档（V1.18）", "",
        "> 数据源：V1.18 SQLite `complete_questions_v2`；一道完整题一条记录，不拆分小问。", "",
        "## 数据摘要", "",
        f"- 完整题：{summary['question_count']}题；来源：{summary['source_count']}个。",
        f"- 难度：{levels}。",
        f"- 答案状态：{answers}。",
        f"- 图片引用：{summary['image_count']}项；结构化校订：{summary['correction_count']}项。",
        "- `missing_from_source` 题目可进入学生版；教师版不得显示伪造答案。", "",
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
            lines.extend([
                f"### {global_index}. `{row['question_id']}`", "",
                f"- 原题号：{row['source_question_number']}；分值：{marks}；难度：Level {row['difficulty_level']}。",
                f"- 主类型：{row['primary_type']}；标签：{tags}。",
                f"- 答案状态：`{row['answer_status']}`；核验：`{row['answer_verification_status']}`。",
                f"- 来源：`{row['source_file']}` / `{row['source_member']}`。", "",
                "#### 原题", "", row["question_text_original"], "",
                "#### 中文审定题干", "", row["question_text_zh_reviewed"], "",
                "#### 答案／解析", "",
                row["solution_verified"] if row["solution_verified"].strip() else "来源未提供答案（`missing_from_source`）。",
                "",
            ])
            if row["audit_notes"].strip():
                lines.extend(["#### 审计说明", "", row["audit_notes"], ""])
    return "\n".join(lines).rstrip() + "\n"


def _v117_import_report(summary: dict[str, object], db_hash: str, csv_hash: str) -> str:
    levels = "、".join(
        f"L{level}×{count}" for level, count in summary["level_counts"].items()
    )
    types = "、".join(
        f"{name}×{count}" for name, count in summary["type_counts"].items()
    )
    return f"""# Joy M2 V1.17 正式入库报告

> 入库日期：2026-08-08（Asia/Singapore）\x20\x20
> Joy审批：已确认 Task 4，批准45道微分应用完整题正式入库。\x20\x20
> 结果：`FORMAL_IMPORT_COMPLETED`

## 一、入库结论

- 正式导入：45/45 道完整题；一道完整题一条记录，未拆分小问。
- 审批状态：45题 `published`、45题 `approved_by_joy`、45题可抽取。
- 自动门禁：P0=0、P1=0；未解决事项0。
- 答案：45/45均为 `source_provided`，并保存核验答案。
- 校订：{summary['correction_count']}项，全部保留原文、订正、理由与证据。
- 标签：本批实际使用{summary['tag_count']}个细分标签；词表V1.1正式生效。

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
- `joy_approval=approved_by_joy`，`approved_at=2026-08-08T20:00:00+08:00`。

## 五、完整性与哈希

- V1.16 SQLite输入SHA-256：`d647244f54e9e54b25ec4885f16c47171c7521552876a5fa925a16d65d8c7714`。
- V1.16正式封包SHA-256：`5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae`。
- V1.17 SQLite SHA-256：`{db_hash}`。
- V1.17 CSV SHA-256：`{csv_hash}`。
- SQLite `integrity_check=ok`；外键异常0。
- SQLite与CSV题号集合一致，均为45个唯一ID。

## 六、后续边界

下一步不是继续修改这45题，而是按同一标准审计并迁移其余452道完整题。全库迁移完成前，旧 `leaf / complete / both` 层仅作为历史兼容层；新组卷流程应优先调用 `selectable_complete_questions_v2`。
"""


def _v118_import_report(summary: dict[str, object], report: dict, db_hash: str, csv_hash: str) -> str:
    levels = "、".join(
        f"L{level}×{count}" for level, count in sorted(summary["level_counts"].items())
    )
    return f"""# Joy M2 V1.18 正式入库报告

> 入库日期：2026-08-08（Asia/Singapore）\x20\x20
> Joy审批：已通过 Task 6 指令授权审计并迁移其余452道完整题。\x20\x20
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

- 审计批次：{report['source_count']}个来源；逐题审计：{report['candidate_count']}题。
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

- V1.17输入SQLite SHA-256：`58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab`。
- V1.18 SQLite SHA-256：`{db_hash}`。
- V1.18 CSV SHA-256：`{csv_hash}`。
- SQLite `integrity_check=ok`；外键异常0；CSV与SQLite均为497个唯一ID。
- V1.17原45题与V1.16历史四表已做逻辑逐字段对比，无变化。

## 六、历史来源边界

V1.16正式交付包未保存若干原始 Mathpix ZIP，因此这些旧批次无法从原始ZIP重新运行历史构建器。Task 6没有伪造档案，而是以V1.17正式SQLite、现有来源文档、V1.16冻结 `source_sha256` 和本次逐题片段SHA-256建立追溯链。后续若补回原始档案，可另开来源再验证任务，不影响V1.18当前数据身份。

## 七、后续建议

V2完整题层现已覆盖497题。下一阶段可先验证组卷器只读取 `selectable_complete_questions_v2`，再评估移除旧 `leaf / complete / both` 兼容层；两项均不在Task 6内执行。
"""


def _v117_project_state() -> str:
    return """# M2 出题系统 — PROJECT_STATE

> 更新时间：2026-08-08（Asia/Singapore）\x20\x20
> 当前正式数据版本：Joy DSE M2 题库 V1.17\x20\x20
> 正式模型：过渡双层；新层坚持一道完整题一条记录，不拆分小问\x20\x20
> 当前唯一优先任务：按新标准审计并迁移其余452道完整题\x20\x20
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


def _v118_project_state(summary: dict[str, object]) -> str:
    return f"""# M2 出题系统 — PROJECT_STATE

> 更新时间：2026-08-08（Asia/Singapore）\x20\x20
> 当前正式数据版本：Joy DSE M2 题库 V1.18\x20\x20
> 正式模型：完整题V2已全量覆盖；一道完整题一条记录，不拆分小问\x20\x20
> 当前状态：Task 6已完成\x20\x20
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


def _render_outputs(request: ExportRequest, database_path: Path) -> dict[str, tuple[bytes, str]]:
    fieldnames, question_rows = _database_rows(database_path, "question_id")
    _, source_rows = _database_rows(database_path, "source_order")
    summary = _database_summary(database_path)
    if summary["question_count"] != request.contract.expected_question_count:
        raise PipelineError("database question count does not match export contract")
    if summary["answer_counts"].get("missing_from_source", 0) != request.contract.expected_missing_answer_count:
        raise PipelineError("database missing-answer count does not match export contract")
    csv_value = csv_bytes(fieldnames, question_rows)
    report = _audit_report_value(request)
    if request.contract.profile == "V1.18":
        knowledge = _v118_knowledge(source_rows, summary)
        import_report = _v118_import_report(
            summary, report, request.database.database.sha256, _sha256_bytes(csv_value)
        )
        state = _v118_project_state(summary)
    else:
        knowledge = _v117_knowledge(source_rows)
        import_report = _v117_import_report(
            summary, request.database.database.sha256, _sha256_bytes(csv_value)
        )
        state = _v117_project_state()
    outputs = {
        "csv": (csv_value, "csv"),
        "knowledge_markdown": (text_bytes(knowledge), "markdown"),
        "import_report": (text_bytes(import_report), "markdown"),
        "project_state": (text_bytes(state), "markdown"),
        "audit_records": (evidence_json_bytes(_audit_records_value(request)), "json"),
        "audit_report": (evidence_json_bytes(report), "json"),
    }
    if request.contract.taxonomy_filename is not None:
        if request.contract.profile != "V1.17":
            raise PipelineError("taxonomy export is only defined for V1.17")
        outputs["taxonomy"] = (evidence_json_bytes(_v117_taxonomy_value()), "json")
    return outputs


def _output_names(request: ExportRequest) -> dict[str, str]:
    names = {
        "csv": request.contract.csv_filename,
        "knowledge_markdown": request.contract.knowledge_markdown_filename,
        "import_report": request.contract.import_report_filename,
        "project_state": request.contract.project_state_filename,
        "audit_records": request.contract.audit_records_filename,
        "audit_report": request.contract.audit_report_filename,
    }
    if request.contract.taxonomy_filename is not None:
        names["taxonomy"] = request.contract.taxonomy_filename
    if any(not name or Path(name).name != name for name in names.values()):
        raise PipelineError("export filenames must be non-empty direct child names")
    if len(set(names.values())) != len(names):
        raise PipelineError("export filenames must be unique")
    return names


def export_database(request: ExportRequest) -> DerivedArtifacts:
    """Write one deterministic set of database and audit-evidence exports."""

    if type(request) is not ExportRequest:
        raise PipelineError("request must be an ExportRequest")
    _batch_audited_records(request)
    database_path = _require_database(request)
    names = _output_names(request)
    targets = {field: request.output_dir / name for field, name in names.items()}
    conflicts = [path for path in targets.values() if path.exists()]
    if conflicts:
        raise OutputConflictError(f"export output already exists: {conflicts[0]}")

    outputs = _render_outputs(request, database_path)
    request.output_dir.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".export-", dir=request.output_dir))
    published: list[Path] = []
    try:
        for field_name, (value, _) in outputs.items():
            (temporary / names[field_name]).write_bytes(value)
        for field_name in names:
            target = targets[field_name]
            if target.exists():
                raise OutputConflictError(f"export output already exists: {target}")
            (temporary / names[field_name]).replace(target)
            published.append(target)
    except Exception:
        for path in published:
            if path.exists():
                path.unlink()
        raise
    finally:
        shutil.rmtree(temporary, ignore_errors=True)

    references = {
        field_name: ArtifactRef(
            path=targets[field_name],
            sha256=_sha256_bytes(value),
            size_bytes=len(value),
            kind=kind,
        )
        for field_name, (value, kind) in outputs.items()
    }
    return DerivedArtifacts(
        csv=references["csv"],
        knowledge_markdown=references["knowledge_markdown"],
        import_report=references["import_report"],
        project_state=references["project_state"],
        taxonomy=references.get("taxonomy"),
        audit_records=references["audit_records"],
        audit_report=references["audit_report"],
    )


def _artifact_map(request: ExportVerificationRequest) -> dict[str, ArtifactRef]:
    result = {
        "csv": request.artifacts.csv,
        "knowledge_markdown": request.artifacts.knowledge_markdown,
        "import_report": request.artifacts.import_report,
        "project_state": request.artifacts.project_state,
        "audit_records": request.artifacts.audit_records,
        "audit_report": request.artifacts.audit_report,
    }
    if request.artifacts.taxonomy is not None:
        result["taxonomy"] = request.artifacts.taxonomy
    return result


def verify_exports(request: ExportVerificationRequest) -> VerificationReport:
    """Verify generated exports without changing any artifact."""

    if type(request) is not ExportVerificationRequest:
        raise PipelineError("request must be an ExportVerificationRequest")
    references = _artifact_map(request)
    expected_names = {
        "csv": request.contract.csv_filename,
        "knowledge_markdown": request.contract.knowledge_markdown_filename,
        "import_report": request.contract.import_report_filename,
        "project_state": request.contract.project_state_filename,
        "audit_records": request.contract.audit_records_filename,
        "audit_report": request.contract.audit_report_filename,
    }
    if request.contract.taxonomy_filename is not None:
        expected_names["taxonomy"] = request.contract.taxonomy_filename
    artifact_parents = {reference.path.parent for reference in references.values()}
    expected_paths_match = (
        set(references) == set(expected_names)
        and all(
            references[field].path.name == name
            for field, name in expected_names.items()
        )
    )
    actual_names: set[str] = set()
    if len(artifact_parents) == 1:
        output_dir = next(iter(artifact_parents))
        if output_dir.is_dir():
            database_path = request.database.database.path
            actual_names = {
                child.name
                for child in output_dir.iterdir()
                if child.is_file() and child != database_path
            }
    checks = [
        _check(
            "expected_file_set",
            expected_paths_match
            and len(artifact_parents) == 1
            and actual_names == set(expected_names.values()),
            "output directory files and ArtifactRef filenames must match the export contract",
        )
    ]
    artifact_bytes: dict[str, bytes | None] = {}
    for field_name, reference in references.items():
        present = reference.path.is_file()
        checks.append(
            _check(
                f"{field_name}_present",
                present,
                "the generated export artifact must exist",
            )
        )
        actual = reference.path.read_bytes() if present else None
        artifact_bytes[field_name] = actual
        checks.append(
            _check(
                f"{field_name}_artifact_identity",
                actual is not None
                and reference.size_bytes == len(actual)
                and reference.sha256 == _sha256_bytes(actual),
                "ArtifactRef size and SHA-256 must match generated bytes",
            )
        )

    database_path = request.database.database.path
    if not database_path.is_file():
        raise InputMissingError(f"export database does not exist: {database_path}")
    fieldnames, database_rows = _database_rows(database_path, "question_id")
    expected_csv = csv_bytes(fieldnames, database_rows)
    csv_value = artifact_bytes["csv"]
    checks.extend((
        _check("csv_bom", csv_value is not None and csv_value.startswith(b"\xef\xbb\xbf"), "CSV must have a UTF-8 BOM"),
        _check("csv_values", csv_value == expected_csv, "CSV bytes must equal ordered SQLite values"),
        _check("csv_row_count", len(database_rows) == request.contract.expected_question_count, "CSV row count must match contract"),
    ))

    records_bytes = artifact_bytes["audit_records"]
    report_bytes = artifact_bytes["audit_report"]
    audit_records = None
    audit_report = None
    if records_bytes is not None:
        try:
            audit_records = json.loads(records_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            pass
    if report_bytes is not None:
        try:
            audit_report = json.loads(report_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            pass
    records_valid = type(audit_records) is list
    report_valid = type(audit_report) is dict
    report_structure_valid = (
        report_valid
        and type(audit_report.get("source_count")) is int
        and type(audit_report.get("candidate_count")) is int
    )
    checks.extend((
        _check("audit_records_json", records_valid and evidence_json_bytes(audit_records) == records_bytes, "audit records must use deterministic evidence JSON"),
        _check("audit_report_json", report_valid and evidence_json_bytes(audit_report) == report_bytes, "audit report must use deterministic evidence JSON"),
        _check("audit_report_structure", report_structure_valid, "audit report must contain exact integer source_count and candidate_count fields"),
        _check("audit_count_agreement", records_valid and report_structure_valid and audit_report.get("candidate_count") == len(audit_records), "audit batch and report counts must agree"),
    ))
    audit_ids = (
        [record.get("question_id") for record in audit_records if type(record) is dict]
        if records_valid
        else []
    )
    _, ordered_rows = _database_rows(database_path, "source_order")
    expected_audit_ids = [
        row["question_id"]
        for row in ordered_rows
        if request.contract.profile == "V1.17" or row["source_order"] > 45
    ]
    checks.append(
        _check("audit_record_order", audit_ids == expected_audit_ids, "audit record IDs and order must match the profile database slice")
    )

    _, source_rows = _database_rows(database_path, "source_order")
    summary = _database_summary(database_path)
    expected_report = None
    if request.contract.profile == "V1.18":
        expected_knowledge = text_bytes(_v118_knowledge(source_rows, summary))
        if report_structure_valid:
            expected_report = text_bytes(
                _v118_import_report(
                    summary, audit_report, request.database.database.sha256, _sha256_bytes(expected_csv)
                )
            )
        expected_state = text_bytes(_v118_project_state(summary))
    else:
        expected_knowledge = text_bytes(_v117_knowledge(source_rows))
        expected_report = text_bytes(
            _v117_import_report(summary, request.database.database.sha256, _sha256_bytes(expected_csv))
        )
        expected_state = text_bytes(_v117_project_state())
    knowledge_bytes = artifact_bytes["knowledge_markdown"]
    try:
        markdown = knowledge_bytes.decode("utf-8") if knowledge_bytes is not None else None
    except UnicodeError:
        markdown = None
    heading_count = (
        len(re.findall(r"^### \d+\. `[^`]+`$", markdown, flags=re.MULTILINE))
        if markdown is not None
        else -1
    )
    missing_count = (
        markdown.count("来源未提供答案（`missing_from_source`）。")
        if markdown is not None
        else -1
    )
    checks.extend((
        _check("markdown_bytes", knowledge_bytes == expected_knowledge, "Markdown must be a deterministic database projection"),
        _check("markdown_headings", heading_count == request.contract.expected_question_count, "Markdown must contain one unique question heading per row"),
        _check("markdown_missing_markers", missing_count == request.contract.expected_missing_answer_count, "Markdown missing-answer markers must match contract"),
        _check("import_report_bytes", expected_report is not None and artifact_bytes["import_report"] == expected_report, "import report must be deterministic"),
        _check("project_state_bytes", artifact_bytes["project_state"] == expected_state, "project state must be deterministic"),
    ))
    if "taxonomy" in references:
        checks.append(
            _check("taxonomy_bytes", artifact_bytes["taxonomy"] == evidence_json_bytes(_v117_taxonomy_value()), "taxonomy must equal the frozen V1.17 projection")
        )
    return VerificationReport(
        status="PASS" if all(check.passed for check in checks) else "FAIL",
        checks=tuple(checks),
    )
