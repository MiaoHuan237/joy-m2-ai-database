import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const root = "/workspace/scratch/25757421d1d8";
const dataDir = `${root}/task4_work/task4_candidate/03_候选数据`;
const outputDir = `${root}/outputs/25757421d1d8`;
const previewDir = `${root}/task4_work/task4_candidate/01_工作簿/previews`;
const outputPath = `${outputDir}/微分应用45题_Task4处理结果_2026-08-08.xlsx`;

const records = JSON.parse(await fs.readFile(`${dataDir}/complete_questions_45_task4.json`, "utf8"));
const taxonomy = JSON.parse(await fs.readFile(`${dataDir}/differentiation_application_taxonomy_v1.1_task4.json`, "utf8"));
const auditLog = JSON.parse(await fs.readFile(`${dataDir}/task4_audit_log.json`, "utf8"));
const validation = JSON.parse(await fs.readFile(`${dataDir}/task4_validation_report.json`, "utf8"));
const difficultySpec = JSON.parse(
  await fs.readFile(`${root}/task4_work/task3_package/05_标准规则/difficulty_levels.json`, "utf8"),
);
const difficulties = difficultySpec.levels;

const wb = Workbook.create();
// Create every sheet before assigning cross-sheet formulas.
const guide = wb.worksheets.add("使用说明");
const resolved = wb.worksheets.add("Task4处理清单");
const all = wb.worksheets.add("45题总表");
const vocab = wb.worksheets.add("标签与难度");
const checks = wb.worksheets.add("验收结果");
const navy = "#193B64";
const paleBlue = "#DCEAF7";
const green = "#E2F0D9";
const greenText = "#236B3B";
const amber = "#FFF2CC";
const red = "#FCE4D6";
const gray = "#F2F4F7";
const border = "#D5DCE5";
const fontName = "Microsoft YaHei";

function title(sheet, address, text) {
  sheet.getRange(address).merge();
  const cell = sheet.getRange(address);
  cell.values = [[text]];
  cell.format = {
    fill: navy,
    font: { name: fontName, size: 17, bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    horizontalAlignment: "left",
  };
  cell.format.rowHeight = 34;
}

function header(range) {
  range.format = {
    fill: navy,
    font: { name: fontName, size: 10, bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    horizontalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: border },
  };
  range.format.rowHeight = 30;
}

function body(range) {
  range.format.font = { name: fontName, size: 9, color: "#263445" };
  range.format.verticalAlignment = "top";
  range.format.wrapText = true;
}

function setWidths(sheet, widths) {
  for (const [address, width] of widths) sheet.getRange(address).format.columnWidth = width;
}

guide.showGridLines = false;
title(guide, "A1:J1", "Joy M2 微分应用45题 · Task 4处理结果");
guide.getRange("A3:J3").values = [[
  "完整题总数", null, "审计通过", null, "待处理", null, "Joy审批", null, "正式入库", null,
]];
guide.getRange("A4:J4").values = [[null, null, null, null, null, null, "未批准", null, "禁止", null]];
guide.getRange("B4").formulas = [["=COUNTA('45题总表'!A4:A48)"]];
guide.getRange("D4").formulas = [["=COUNTIF('45题总表'!J4:J48,\"audit_passed\")"]];
guide.getRange("F4").formulas = [["=COUNTIF('45题总表'!J4:J48,\"audit_pending\")"]];
for (const range of ["A3:B3", "C3:D3", "E3:F3", "G3:H3", "I3:J3"]) {
  guide.getRange(range).merge();
  guide.getRange(range).format = { fill: paleBlue, font: { name: fontName, bold: true, color: navy } };
}
for (const range of ["A4:B4", "C4:D4", "E4:F4", "G4:H4", "I4:J4"]) guide.getRange(range).merge();
guide.getRange("A4:J4").format = {
  font: { name: fontName, size: 14, bold: true, color: navy },
  horizontalAlignment: "center",
  verticalAlignment: "center",
};
guide.getRange("G4:H4").format.fill = amber;
guide.getRange("I4:J4").format.fill = red;
guide.getRange("A6:J6").merge();
guide.getRange("A6").values = [["本阶段边界"]];
guide.getRange("A6:J6").format = { fill: paleBlue, font: { name: fontName, bold: true, color: navy } };
const guideRows = [
  ["数据单位", "一道完整题一条记录，全部小问保留在题内，不拆分。"],
  ["已处理", "14题答案来源映射、3题分值、教材/甲部/乙部内容订正、2题标签词表缺口。"],
  ["技术结果", "45题均通过技术审计；P0=0，P1=0。"],
  ["审批结果", "Joy尚未批准正式入库，本文件只是Task 4审阅候选。"],
  ["禁止操作", "不得修改正式SQLite/CSV，不得以旧V1.13工作副本写入。"],
  ["下一步", "Joy确认本包后，才能生成正式导入候选并再次验收。"],
];
guide.getRange("A7:J12").values = guideRows.map(([label, text]) => [label, text, null, null, null, null, null, null, null, null]);
for (let row = 7; row <= 12; row++) guide.getRange(`B${row}:J${row}`).merge();
body(guide.getRange("A7:J12"));
guide.getRange("A7:A12").format.font = { name: fontName, bold: true, color: navy };
guide.getRange("A7:J12").format.borders = { preset: "inside", style: "thin", color: border };
guide.freezePanes.freezeRows(1);
setWidths(guide, [["A:A", 16], ["B:J", 13]]);

resolved.showGridLines = false;
title(resolved, "A1:K1", "Task 4 · 21道待决题处理清单");
const resolvedHeaders = [
  "题目ID", "分区", "处理类别", "总分", "标签", "答案来源文件", "答案来源成员", "答案成员SHA-256", "处理结论", "技术状态", "Joy审批",
];
resolved.getRange("A3:K3").values = [resolvedHeaders];
header(resolved.getRange("A3:K3"));
const recordById = new Map(records.map((row) => [row.question_id, row]));
const resolvedRows = auditLog.map((entry) => {
  const row = recordById.get(entry.question_id);
  const changed = new Set(entry.changed_fields);
  const categories = [];
  if (["solution_source_file", "solution_source_member", "solution_source_member_sha256"].some((f) => changed.has(f))) categories.push("答案来源映射");
  if (changed.has("marks_total")) categories.push("分值补录");
  if (changed.has("tags")) categories.push("标签词表");
  if (changed.has("review_checks")) categories.push("内容订正");
  return [
    row.question_id,
    row.source_section,
    categories.join("；") || "审计状态关闭",
    row.marks_total,
    row.tags.join("；"),
    row.solution_source_file,
    row.solution_source_member,
    row.solution_source_member_sha256,
    entry.resolution,
    "技术审计通过",
    "未批准",
  ];
});
resolved.getRange(`A4:K${3 + resolvedRows.length}`).values = resolvedRows;
body(resolved.getRange(`A4:K${3 + resolvedRows.length}`));
resolved.getRange(`J4:J${3 + resolvedRows.length}`).format = { fill: green, font: { name: fontName, bold: true, color: greenText } };
resolved.getRange(`K4:K${3 + resolvedRows.length}`).format = { fill: amber, font: { name: fontName, bold: true, color: "#8A6500" } };
resolved.tables.add(`A3:K${3 + resolvedRows.length}`, true, "Task4ResolvedTable").style = "TableStyleMedium2";
resolved.freezePanes.freezeRows(3);
resolved.freezePanes.freezeColumns(2);
setWidths(resolved, [
  ["A:A", 27], ["B:B", 12], ["C:C", 22], ["D:D", 8], ["E:E", 28], ["F:F", 25], ["G:G", 38], ["H:H", 68], ["I:I", 48], ["J:K", 14],
]);

all.showGridLines = false;
title(all, "A1:K1", "微分应用45道完整题 · Task 4候选总表");
const allHeaders = ["题目ID", "分区", "原题号", "总分", "Level", "主类型", "细分标签", "答案状态", "答案来源", "审计状态", "Joy审批"];
all.getRange("A3:K3").values = [allHeaders];
header(all.getRange("A3:K3"));
const allRows = records.map((row) => [
  row.question_id,
  row.source_section,
  row.source_question_number,
  row.marks_total,
  row.difficulty_level,
  row.primary_type,
  row.tags.join("；"),
  row.answer_status,
  row.solution_source_file,
  row.record_status,
  "未批准",
]);
all.getRange("A4:K48").values = allRows;
body(all.getRange("A4:K48"));
all.getRange("J4:J48").format = { fill: green, font: { name: fontName, bold: true, color: greenText } };
all.getRange("K4:K48").format = { fill: amber, font: { name: fontName, bold: true, color: "#8A6500" } };
all.tables.add("A3:K48", true, "AllQuestionsTable").style = "TableStyleMedium2";
all.freezePanes.freezeRows(3);
all.freezePanes.freezeColumns(2);
setWidths(all, [["A:A", 27], ["B:B", 12], ["C:C", 17], ["D:E", 8], ["F:F", 18], ["G:G", 42], ["H:H", 19], ["I:I", 25], ["J:K", 15]]);

vocab.showGridLines = false;
title(vocab, "A1:H1", "微分应用受控标签 V1.1 与 Joy Level 1–5");
vocab.getRange("A3:C3").values = [["序号", "细分标签", "使用原则"]];
header(vocab.getRange("A3:C3"));
const tagRows = taxonomy.tags.map((tag, i) => [i + 1, tag, "只标题目明确要求的能力"]);
vocab.getRange(`A4:C${3 + tagRows.length}`).values = tagRows;
body(vocab.getRange(`A4:C${3 + tagRows.length}`));
vocab.getRange("E3:H3").values = [["Level", "判定标准", "典型表现", "辅助分参考"]];
header(vocab.getRange("E3:H3"));
const difficultyRows = difficulties.map((d) => [d.level, d.standard, d.example, d.score_reference]);
vocab.getRange(`E4:H${3 + difficultyRows.length}`).values = difficultyRows;
body(vocab.getRange(`E4:H${3 + difficultyRows.length}`));
vocab.getRange("A36:C36").merge();
vocab.getRange("A36").values = [["V1.1新增：全局最小值、从基本原理求导、导数为正区间"]];
vocab.getRange("A36:C36").format = { fill: green, font: { name: fontName, bold: true, color: greenText }, wrapText: true };
vocab.tables.add(`A3:C${3 + tagRows.length}`, true, "TagVocabularyTable").style = "TableStyleMedium2";
vocab.tables.add(`E3:H${3 + difficultyRows.length}`, true, "DifficultyTable").style = "TableStyleMedium2";
vocab.freezePanes.freezeRows(3);
setWidths(vocab, [["A:A", 8], ["B:B", 24], ["C:C", 32], ["D:D", 3], ["E:E", 8], ["F:F", 46], ["G:G", 42], ["H:H", 20]]);

checks.showGridLines = false;
title(checks, "A1:F1", "Task 4 自动验收与边界");
checks.getRange("A3:B9").values = [
  ["项目", "结果"],
  ["验收状态", validation.status],
  ["完整题", validation.summary.total],
  ["audit_passed", validation.summary.audit_passed],
  ["P0", validation.summary.p0],
  ["P1", validation.summary.p1],
  ["正式导入批准", "0（未批准）"],
];
header(checks.getRange("A3:B3"));
body(checks.getRange("A4:B9"));
checks.getRange("B4:B8").format = { fill: green, font: { name: fontName, bold: true, color: greenText } };
checks.getRange("B9").format = { fill: amber, font: { name: fontName, bold: true, color: "#8A6500" } };
checks.getRange("A11:F11").merge();
checks.getRange("A11").values = [["边界说明"]];
checks.getRange("A11:F11").format = { fill: paleBlue, font: { name: fontName, bold: true, color: navy } };
checks.getRange("A12:F13").merge();
checks.getRange("A12").values = [[validation.boundary + " 正式SQLite/CSV及Task 3输入均未修改。"]];
checks.getRange("A12:F13").format = { fill: gray, font: { name: fontName, size: 11, color: "#263445" }, wrapText: true, verticalAlignment: "center" };
checks.getRange("A15:F15").merge();
checks.getRange("A15").values = [["已知基线限制"]];
checks.getRange("A15:F15").format = { fill: paleBlue, font: { name: fontName, bold: true, color: navy } };
checks.getRange("A16:F18").merge();
checks.getRange("A16").values = [["Task 3 ZIP 未包含 test_audit_package.py 所依赖的 build_audit_package.py，因此其19项基础测试无法从交付包独立复跑；Task 4采用自包含测试与验证器，不把该旧包缺口计为题目数据失败。"]];
checks.getRange("A16:F18").format = { fill: amber, font: { name: fontName, size: 10, color: "#6B4F00" }, wrapText: true, verticalAlignment: "center" };
checks.freezePanes.freezeRows(1);
setWidths(checks, [["A:A", 24], ["B:B", 38], ["C:F", 18]]);

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
const workbookOutput = await SpreadsheetFile.exportXlsx(wb);
await workbookOutput.save(outputPath);

const sheetNames = ["使用说明", "Task4处理清单", "45题总表", "标签与难度", "验收结果"];
for (let i = 0; i < sheetNames.length; i++) {
  const png = await wb.render({ sheetName: sheetNames[i], autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(`${previewDir}/${i + 1}_${sheetNames[i]}.png`, new Uint8Array(await png.arrayBuffer()));
}

const summary = await wb.inspect({
  kind: "table",
  range: "使用说明!A1:J12",
  include: "values,formulas",
  tableMaxRows: 14,
  tableMaxCols: 12,
  maxChars: 5000,
});
const resolvedCheck = await wb.inspect({
  kind: "table",
  range: "Task4处理清单!A1:K24",
  include: "values,formulas",
  tableMaxRows: 25,
  tableMaxCols: 11,
  maxChars: 9000,
});
const errors = await wb.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
  maxChars: 4000,
});
console.log(JSON.stringify({ outputPath, sheetNames }));
console.log(summary.ndjson);
console.log(resolvedCheck.ndjson);
console.log(errors.ndjson);
