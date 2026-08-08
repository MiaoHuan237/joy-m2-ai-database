import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const auditRoot = process.argv[2];
const previewDir = process.argv[3];
if (!auditRoot || !previewDir) throw new Error("Usage: node build_audit_workbook.mjs AUDIT_ROOT PREVIEW_DIR [RECORDS_JSON] [OUTPUT_XLSX]");

const derived = path.join(auditRoot, "derived");
const recordsPath = process.argv[4] || path.join(derived, "complete_questions_45.json");
const outputPath = process.argv[5] || path.join(derived, "微分应用45题审计工作表.xlsx");
const records = JSON.parse(await fs.readFile(recordsPath, "utf8"));
const taxonomy = JSON.parse(await fs.readFile(path.join(derived, "differentiation_application_taxonomy.json"), "utf8"));
const difficulty = JSON.parse(await fs.readFile(path.join(derived, "difficulty_levels.json"), "utf8"));
const acceptance = JSON.parse(await fs.readFile(path.join(derived, "acceptance_rules.json"), "utf8"));

const workbook = Workbook.create();
const instructions = workbook.worksheets.add("使用说明");
const audit = workbook.worksheets.add("审计工作表");
const taxonomySheet = workbook.worksheets.add("标签词表");
const difficultySheet = workbook.worksheets.add("难度标准");
const rulesSheet = workbook.worksheets.add("验收规则");

const navy = "#17365D";
const blue = "#D9EAF7";
const paleBlue = "#EAF2F8";
const paleYellow = "#FFF2CC";
const paleGreen = "#E2F0D9";
const paleRed = "#FCE4D6";
const grey = "#E7E6E6";
const text = "#1F2937";
const cjkFont = "Noto Sans CJK SC";

const statusCounts = records.reduce((acc, record) => {
  const key = record.record_status || "audit_pending";
  acc[key] = (acc[key] || 0) + 1;
  return acc;
}, {});

function checkText(value) {
  return {
    pass: "通过",
    revised: "已规范",
    issue: "有疑点",
    unknown: "分值未知",
    not_required: "不适用",
    missing: "缺失",
    needs_correction: "需订正",
    blocked: "阻断",
  }[value] || "待检查";
}

function titleBand(sheet, range, value) {
  sheet.getRange(range).merge();
  sheet.getRange(range).values = [[value]];
  sheet.getRange(range).format = {
    fill: navy,
    font: { name: cjkFont, bold: true, color: "#FFFFFF", size: 16 },
    verticalAlignment: "center",
  };
  sheet.getRange(range).format.rowHeightPx = 34;
}

// 使用说明
instructions.showGridLines = false;
titleBand(instructions, "A1:F1", "Joy M2 微分应用45题完整题审计工作表");
instructions.getRange("A3:B11").values = [
  ["项目", "说明"],
  ["当前阶段", `Task 3逐题复核；通过${statusCounts.audit_passed || 0}题、待修${statusCounts.audit_pending || 0}题、阻断${statusCounts.blocked || 0}题。Joy确认前不正式入库。`],
  ["审计单位", "一道完整题一行，保留全部小问，不拆分。"],
  ["推荐顺序", "先检查题目边界与英中内容，再检查答案、图片、标签与难度。"],
  ["新主类型", "从5个受控主类型中单选。"],
  ["新标签", "从“标签词表”选取；多标签用中文分号“；”分隔。"],
  ["新Level", "按整题最高稳定认知要求评为1–5，并填写判级证据。"],
  ["自动验收", "P0阻断；P1人工复核；P2提示。"],
  ["正式入库", "Joy确认前不得把记录改为 approved_for_import，也不得修改正式SQLite/CSV。"],
];
instructions.getRange("A3:B3").format = { fill: blue, font: { bold: true, color: text }, borders: { preset: "outside", style: "thin", color: "#9CA3AF" } };
instructions.getRange("A4:B11").format = { font: { color: text, size: 10 }, wrapText: true, verticalAlignment: "top", borders: { preset: "inside", style: "thin", color: "#D1D5DB" } };
instructions.getRange("A3:A11").format.font = { bold: true, color: text };
instructions.getRange("A3:A11").format.columnWidthPx = 130;
instructions.getRange("B3:B11").format.columnWidthPx = 620;
instructions.getRange("A4:B11").format.rowHeightPx = 40;

// 审计工作表
audit.showGridLines = false;
const headers = [
  "question_id", "原题号", "来源分区", "来源标题", "旧Level", "旧标签", "答案状态", "总分", "图片", "重复状态", "重复参照",
  "题目边界完整", "英文题干准确", "中文自然且含义一致", "公式符号单位准确", "小问顺序与分值完整", "必要图片正确", "答案与题目对应", "答案数学复核",
  "新主类型", "新标签（；分隔）", "新Level", "判级证据", "疑点", "订正内容", "订正证据", "复核状态", "自动验收结果", "Joy审批状态", "record_status",
];
const matrix = [headers];
for (const record of records) {
  const checks = record.review_checks || {};
  const corrections = record.corrections || [];
  const correctionText = corrections.map((item) => `${item.field || ""}: ${item.corrected || ""}`).join("；");
  const correctionEvidence = corrections.map((item) => item.evidence || item.reason || "").join("；");
  const reviewStatus = record.record_status || "audit_pending";
  matrix.push([
    record.question_id,
    record.source_question_number,
    record.source_section,
    record.source_heading,
    record.old_difficulty,
    record.old_tags.join("；"),
    record.answer_status,
    record.marks_total,
    record.image_paths.map((item) => item.path).join("；"),
    record.duplicate_status,
    record.duplicate_reference,
    checkText(checks.question_boundary),
    checkText(checks.english_text),
    checkText(checks.chinese_text),
    checkText(checks.formula_symbols_units),
    checkText(checks.subparts_and_marks),
    checkText(checks.necessary_images),
    checkText(checks.answer_pairing),
    checkText(checks.answer_mathematics),
    record.primary_type || "",
    (record.tags || []).join("；"),
    record.difficulty_level ?? null,
    record.difficulty_evidence || "",
    (record.unresolved_issues || []).join("；"),
    correctionText,
    correctionEvidence,
    reviewStatus,
    reviewStatus === "audit_passed" ? "逐题复核通过" : reviewStatus === "blocked" ? "阻断" : "需人工确认/订正",
    "未确认",
    reviewStatus,
  ]);
}
audit.getRangeByIndexes(0, 0, matrix.length, headers.length).values = matrix;
audit.freezePanes.freezeRows(1);
audit.freezePanes.freezeColumns(3);
audit.getRange("A1:AD1").format = {
  fill: navy,
  font: { bold: true, color: "#FFFFFF", size: 10 },
  wrapText: true,
  verticalAlignment: "center",
  horizontalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#9CA3AF" },
};
audit.getRange("A1:AD1").format.rowHeightPx = 42;
audit.getRange("A2:AD46").format = {
  font: { color: text, size: 9 },
  verticalAlignment: "top",
  wrapText: true,
  borders: { preset: "inside", style: "thin", color: "#E5E7EB" },
};
audit.getRange("A2:K46").format.fill = "#F8FAFC";
audit.getRange("L2:AD46").format.fill = "#FFFFFF";
audit.getRange("A2:AD46").format.rowHeightPx = 46;

const widths = [170, 100, 90, 190, 65, 240, 110, 60, 200, 100, 110, 95, 95, 125, 115, 130, 100, 105, 110, 130, 250, 70, 260, 220, 250, 230, 110, 140, 110, 110];
for (let col = 0; col < widths.length; col += 1) {
  audit.getRangeByIndexes(0, col, 46, 1).format.columnWidthPx = widths[col];
}

const reviewValues = ["待检查", "通过", "已规范", "有疑点", "分值未知", "不适用", "缺失", "需订正", "阻断"];
for (const col of ["L", "M", "N", "O", "P", "Q", "R", "S"]) {
  audit.getRange(`${col}2:${col}46`).dataValidation = { rule: { type: "list", values: reviewValues } };
}
audit.getRange("T2:T46").dataValidation = { rule: { type: "list", values: taxonomy.primary_types } };
audit.getRange("V2:V46").dataValidation = { rule: { type: "whole", operator: "between", formula1: 1, formula2: 5 } };
audit.getRange("AA2:AA46").dataValidation = { rule: { type: "list", values: ["audit_pending", "audit_passed", "blocked"] } };
audit.getRange("AC2:AC46").dataValidation = { rule: { type: "list", values: ["未确认", "确认预检", "退回修改"] } };
audit.getRange("AD2:AD46").dataValidation = { rule: { type: "list", values: ["audit_pending", "audit_passed", "blocked", "approved_for_import"] } };

for (const col of ["L", "M", "N", "O", "P", "Q", "R", "S"]) {
  const range = audit.getRange(`${col}2:${col}46`);
  range.conditionalFormats.add("containsText", { text: "待检查", format: { fill: paleYellow, font: { color: "#7F6000" } } });
  range.conditionalFormats.add("containsText", { text: "通过", format: { fill: paleGreen, font: { color: "#375623" } } });
  range.conditionalFormats.add("containsText", { text: "已规范", format: { fill: paleGreen, font: { color: "#375623" } } });
  range.conditionalFormats.add("containsText", { text: "分值未知", format: { fill: paleYellow, font: { color: "#7F6000" } } });
  range.conditionalFormats.add("containsText", { text: "有疑点", format: { fill: paleRed, font: { color: "#9C0006" } } });
  range.conditionalFormats.add("containsText", { text: "需订正", format: { fill: paleRed, font: { color: "#9C0006" } } });
  range.conditionalFormats.add("containsText", { text: "缺失", format: { fill: paleRed, font: { color: "#9C0006" } } });
  range.conditionalFormats.add("containsText", { text: "阻断", format: { fill: paleRed, font: { bold: true, color: "#9C0006" } } });
}
audit.getRange("AA2:AA46").conditionalFormats.add("containsText", { text: "audit_pending", format: { fill: paleYellow, font: { color: "#7F6000" } } });
audit.getRange("AD2:AD46").conditionalFormats.add("containsText", { text: "approved_for_import", format: { fill: paleRed, font: { bold: true, color: "#9C0006" } } });
const table = audit.tables.add("A1:AD46", true, "DifferentiationAudit45");
table.style = "TableStyleMedium2";
table.showBandedRows = true;

// 标签词表
taxonomySheet.showGridLines = false;
titleBand(taxonomySheet, "A1:D1", "微分应用受控标签词表");
taxonomySheet.getRange("A3:B8").values = [
  ["主类型", "使用原则"],
  ...taxonomy.primary_types.map((item) => [item, item === "综合微分应用" ? "跨两个以上独立板块且无明显主目标时使用" : "按整题核心教学目标选择"]),
];
taxonomySheet.getRange("A11:C11").values = [["序号", "细分标签", "规则"]];
taxonomySheet.getRangeByIndexes(11, 0, taxonomy.tags.length, 3).values = taxonomy.tags.map((tag, index) => [index + 1, tag, "只标题目明确要求的能力"]);
taxonomySheet.getRange("A3:B3").format = { fill: blue, font: { bold: true, color: text } };
taxonomySheet.getRange("A11:C11").format = { fill: blue, font: { bold: true, color: text } };
taxonomySheet.getRange(`A3:C${11 + taxonomy.tags.length}`).format.wrapText = true;
taxonomySheet.getRange("A:A").format.columnWidthPx = 90;
taxonomySheet.getRange("B:B").format.columnWidthPx = 220;
taxonomySheet.getRange("C:C").format.columnWidthPx = 300;

// 难度标准
difficultySheet.showGridLines = false;
titleBand(difficultySheet, "A1:E1", "Joy Level 1–5 难度标准");
difficultySheet.getRange("A3:D8").values = [
  ["Level", "判定标准", "微分应用典型表现", "辅助分参考"],
  ...difficulty.levels.map((item) => [item.level, item.standard, item.example, item.score_reference]),
];
difficultySheet.getRange("A3:D3").format = { fill: blue, font: { bold: true, color: text }, wrapText: true };
difficultySheet.getRange("A4:D8").format = { wrapText: true, verticalAlignment: "top", font: { color: text, size: 10 } };
difficultySheet.getRange("A:A").format.columnWidthPx = 70;
difficultySheet.getRange("B:B").format.columnWidthPx = 330;
difficultySheet.getRange("C:C").format.columnWidthPx = 360;
difficultySheet.getRange("D:D").format.columnWidthPx = 250;
difficultySheet.getRange("A4:D8").format.rowHeightPx = 64;
difficultySheet.getRange("A10:D13").values = [
  ["评分维度", "概念数", "推理链长度", "建模强度"],
  ["评分维度", "代数负担", "条件处理", "易错风险"],
  ["每维分值", "0", "1", "2"],
  ["提醒", "总分只作参考", "整题必须写判级证据", "不能仅因计算繁琐判L5"],
];
 difficultySheet.getRange("A10:D13").format = { fill: paleBlue, wrapText: true, font: { color: text } };

// 验收规则
rulesSheet.showGridLines = false;
titleBand(rulesSheet, "A1:D1", "自动验收规则 P0 / P1 / P2");
rulesSheet.getRange("A3:D3").values = [["规则编号", "级别", "检查项", "条件"]];
rulesSheet.getRangeByIndexes(3, 0, acceptance.rules.length, 4).values = acceptance.rules.map((rule) => [rule.rule_id, rule.severity, rule.name, rule.condition]);
rulesSheet.getRange("A3:D3").format = { fill: blue, font: { bold: true, color: text } };
rulesSheet.getRange(`A4:D${3 + acceptance.rules.length}`).format = { wrapText: true, verticalAlignment: "top", font: { color: text, size: 10 } };
rulesSheet.getRange("A:A").format.columnWidthPx = 180;
rulesSheet.getRange("B:B").format.columnWidthPx = 70;
rulesSheet.getRange("C:C").format.columnWidthPx = 160;
rulesSheet.getRange("D:D").format.columnWidthPx = 520;
rulesSheet.getRange(`A4:D${3 + acceptance.rules.length}`).format.rowHeightPx = 38;
rulesSheet.getRange(`B4:B${3 + acceptance.rules.length}`).conditionalFormats.add("containsText", { text: "P0", format: { fill: paleRed, font: { bold: true, color: "#9C0006" } } });
rulesSheet.getRange(`B4:B${3 + acceptance.rules.length}`).conditionalFormats.add("containsText", { text: "P1", format: { fill: paleYellow, font: { bold: true, color: "#7F6000" } } });
rulesSheet.getRange(`B4:B${3 + acceptance.rules.length}`).conditionalFormats.add("containsText", { text: "P2", format: { fill: grey, font: { bold: true, color: "#404040" } } });

for (const sheet of [taxonomySheet, difficultySheet, rulesSheet]) sheet.freezePanes.freezeRows(3);

for (const sheet of [instructions, audit, taxonomySheet, difficultySheet, rulesSheet]) {
  const used = sheet.getUsedRange();
  if (used) used.format.font = { name: cjkFont };
}

await fs.mkdir(previewDir, { recursive: true });
const inspect = await workbook.inspect({ kind: "workbook,sheet,table", maxChars: 7000, tableMaxRows: 5, tableMaxCols: 8, tableMaxCellChars: 80 });
await fs.writeFile(path.join(previewDir, "inspect.ndjson"), inspect.ndjson, "utf8");
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" });
await fs.writeFile(path.join(previewDir, "formula_errors.ndjson"), errors.ndjson, "utf8");

for (const sheetName of ["使用说明", "审计工作表", "标签词表", "难度标准", "验收规则"]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: sheetName === "审计工作表" ? 0.7 : 1.2, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, recordsPath, sheets: 5, rows: records.length, statusCounts }));
