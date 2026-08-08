# Task 3 教材例题逐题审计报告

## 核对方法

本次仅审计 `complete_questions_45.json` 中 `source_section="教材例题"` 的 8 道完整题，不拆分小问，也未修改任何现有题库、数据库、CSV、来源 ZIP 或派生文件。

逐题执行了以下核对：

1. 对照 `review_contract.md`、完整题入库标准、受控分类词表与 Joy Level 定义，检查所有必填字段和枚举。
2. 回查冻结来源 `M2Quick Drill-微分法的应用.mmd.zip` 的原始 MMD 题干、分值与题解行；同时核对 `v116_import_snapshot.json` 中已登记的来源校订。
3. 目视检查 Q1、Q3、Q5、Q6 对应的 4 张嵌入图。四图都只是“题解”页眉，不承载题目条件，故 8 题均判为 `necessary_images=not_required`。
4. 独立复算每题的导数、切线/法线、驻点及变号、渐近线、最值和相关变化率；用数值代入交叉检查关键值与 Q8 的切点等号。
5. 分类只使用受控主类型和受控标签；Level 按整题最高稳定认知要求评定，六维各项均在 0–2。

## 题数与状态

| 项目 | 数量 |
|---|---:|
| 审计题数 | 8 |
| `audit_passed` | 5 |
| `audit_pending` | 3 |
| `blocked` | 0 |

待修/待决题为 Q3、Q6、Q8；没有题目因边界、核心条件、必要图片或答案缺失而阻断。

## 逐题结论

| 题号 | 状态 | 主类型 | Level | 结论摘要 |
|---|---|---|---:|---|
| M2QD-DA-EXAMPLE-Q1 | 通过 | 切线与法线 | 3 | 答案正确；补记来源 MMD 切线斜率式的既有 OCR 校订。 |
| M2QD-DA-EXAMPLE-Q2 | 通过 | 极值与曲线性质 | 3 | 极大点 $(-3,-3)$ 正确；来源没有分值，保持 `unknown`。 |
| M2QD-DA-EXAMPLE-Q3 | 待决 | 最值与最优化 | 4 | 全域全局最小值 $-1152$ 正确；受控词表无对应细标签，需 Joy 决定扩词或接受 `tags=[]`。 |
| M2QD-DA-EXAMPLE-Q4 | 通过 | 极值与曲线性质 | 3 | 两个拐点结论正确；补记来源题解漏印二阶导数的既有校订。 |
| M2QD-DA-EXAMPLE-Q5 | 通过 | 极值与曲线性质 | 2 | 渐近线 $x=-2$、$y=x+3$ 均正确。 |
| M2QD-DA-EXAMPLE-Q6 | 待修 | 综合微分应用 | 5 | 数学答案正确；英文把 `$C$` 与 `$L$` 错并入同一数学环境，须回写并保留原文。 |
| M2QD-DA-EXAMPLE-Q7 | 通过 | 变率 | 4 | 面积变率 $-2$ 正确；补记来源变率方程被 OCR 截断的既有校订。 |
| M2QD-DA-EXAMPLE-Q8 | 待修 | 综合微分应用 | 4 | 切点 $x=\pi$ 处 $G=L$；严谨结论应为整段“不高于”，且除切点外严格低于。 |

## 发现的问题与证据

### 已有来源校订，现补齐逐题轨迹

- Q1：原 MMD 第 364 行把切点到外点的斜率写成错误的分式；正确式须同时减去 20，并使用分母 $h-10$。该校订已在 `v116_import_snapshot.json` 以 `ex-3.1-tangent-slope` 登记，独立联立得到 $h=6,30$，定义域只保留 $h=6$。
- Q4：原题解 (a) 漏印 $d^2y/dx^2$；校订 `ex-3.4-second-derivative` 给出的 $(-x^2+5x-4)e^{-x}$ 经独立求导正确。
- Q6：原 MMD 直接给出 $dA/dt<e/\sqrt{e^2}=1$，其 `<1` 结论本身正确。审计答案补足链式推导，并给出更紧精确上界 $dA/dt\le e/\sqrt{e^2+1}<1$；这属于推导补全与上界精化，不判为数学错误。缺少原扫描页，故不采用 Mathpix/OCR 归因。
- Q7：原 MMD 的圆面积求导式被 OCR 截断；`ex-3.7-rate-equation` 的重建式复算后给出 $dS/dt=-2$。

### 本轮新增疑点

- Q3 的能力是全域上的全局最小值，但当前受控标签只有 `区间最值`，语义不符，且没有“全局最值”或“全局最小值”标签。现保持 `tags=[]` 与 `audit_pending`，待 Joy 决定扩充词表或接受空标签。
- Q6 英文原题写成 `lying on $C . L$ is a line`。中文来源清楚表明应为 `lying on $C$. $L$ is a line`。冻结 MMD 的数学定界有误，但因缺少原扫描页不进一步归因于 Mathpix；当前英文原题尚未订正，故为 `audit_pending`。
- Q8 (c)(ii) 声称图像在整个开区间内位于切线下方，但 $L$ 正是 $x=\pi$ 处的切线，故 $f(\pi)=L(\pi)=0$。严格凹性只推出 $G\le L$，且在 $x\ne\pi$ 时严格小于。英文、中文及来源答案均应同步改严谨；是否沿用教材的宽松措辞须由 Joy 决定。

### 非问题但需说明

- Q2 来源没有印分值，因此 `subparts_and_marks=unknown`，不猜测分值。
- Q6 的来源未印例题标题；`EX-3.6 (editorial stable identifier)` 是既有审计中的内部稳定标识，不冒充印刷标题。
- Q4 的改编匹配证据指向现有题 `2022-Q4`；Q7 保留 `DSE-2020-Q6` 历史参考；Q8 保留 `DSE-2023-Q9` 改编关系。

## 自检命令

在仓库根目录运行：

```bash
jq -e '
  length == 8 and
  ([.[].question_id] | unique | length == 8) and
  all(.[]; .source_section == "教材例题") and
  all(.[]; (.record_status == "audit_passed" or .record_status == "audit_pending" or .record_status == "blocked")) and
  all(.[]; (.difficulty_level >= 1 and .difficulty_level <= 5))
' V1.16_complete_question_audit/derived/task3_review/review_教材例题.json

jq -r 'group_by(.record_status) | map({status: .[0].record_status, count: length})' \
  V1.16_complete_question_audit/derived/task3_review/review_教材例题.json

jq -e --slurpfile taxonomy V1.16_complete_question_audit/derived/differentiation_application_taxonomy.json '
  all(.[]; (.primary_type as $p | $taxonomy[0].primary_types | index($p)) != null) and
  all(.[]; all(.tags[]; (. as $t | $taxonomy[0].tags | index($t)) != null))
' V1.16_complete_question_audit/derived/task3_review/review_教材例题.json
```

另按 `pre_task_hashes.json` 逐项重算受保护文件的字节数和 SHA-256，确认均与任务前基线一致。
