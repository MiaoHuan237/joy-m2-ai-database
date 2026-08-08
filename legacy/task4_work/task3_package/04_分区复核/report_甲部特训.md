# Joy M2 V1.16 微分应用45题 Task 3——甲部特训逐题审计报告

## 结论

- 审计范围：`source_section="甲部特训"` 的17道完整题，题号 `M2QD-DA-PARTA-Q1` 至 `M2QD-DA-PARTA-Q17`。
- 通过：14题。
- 待修：3题（Q6、Q13、Q16）。
- 阻断：0题。
- 总体状态：`DONE_WITH_CONCERNS`。三题均可由现有题目条件独立求解，数学疑点已有明确证据和经复算的订正，不构成阻断；另有一项未关闭的Joy决策：Q13是否继续保持空标签，或在后续词表中增补“从基本原理求导/切线斜率为正区间”标签。

## 核对方法

1. 完整读取并遵守 `review_contract.md`、`完整题入库标准_V1.0.md`、`differentiation_application_taxonomy.json` 与 `difficulty_levels.json`。
2. 从 `complete_questions_45.json` 仅抽取 `source_section="甲部特训"` 的17条，逐题核对完整题边界、英文、中文、公式、符号、单位、小问、分值、图片映射、题答配对和答案数学。
3. 不解压、不修改冻结来源；以 `unzip -p` 回读：
   - `frozen_sources/M2Quick Drill-微分法的应用.mmd.zip` 内题目MMD第1005–1207行；
   - `frozen_sources/微分的应用甲部.mmd.zip` 内答案MMD第450–1079行。
4. 查看甲部题组在答案MMD中实际依赖的全部图像：
   - Q10作图：`c2e97ff4-9258-43ff-802f-ac95d2c5c0e2-13_608_699_242_347.jpg`；
   - Q11作图：`c2e97ff4-9258-43ff-802f-ac95d2c5c0e2-14_525_610_242_345.jpg`；
   - Q14导函数直线图：`c2e97ff4-9258-43ff-802f-ac95d2c5c0e2-15_334_509_1549_1208.jpg`；
   - Q14的 `c2e97ff4-9258-43ff-802f-ac95d2c5c0e2-15_37_48_1553_1081.jpg` 仅为“1M”得分标记碎片。
   17道题的题干本身均不依赖外加图片，因此 `necessary_images` 均为 `not_required`；Q10、Q11的作图答案已依据原图和独立曲线分析双重核对。
5. 对17题全部独立复算，包括隐函数切线、未知切点、局部/区间极值、渐近线、拐点、曲线作图、相关变率及数值近似。Q17另以数值计算复核为 `0.220656...`，三位有效数字为 `0.221`。
6. 主类型和标签只使用受控词表，且只标题目明确考查的能力。Q13考查“从基本原理求导”和“切线斜率为正的区间”，现有受控标签没有对应项，因此暂保留 `tags=[]`，未硬贴近似但不准确的标签；此词表缺口已写入 `unresolved_issues`，须由Joy决定保持空标签或后续增补受控标签。
7. Level按整题最高稳定认知要求判断；六维评分每维仅取0、1、2。

## 状态统计

| 记录状态 | 题数 | 题号 |
|---|---:|---|
| `audit_passed` | 14 | Q1–Q5、Q7–Q12、Q14–Q15、Q17 |
| `audit_pending` | 3 | Q6、Q13、Q16 |
| `blocked` | 0 | 无 |

## 发现的问题与证据

### Q6：来源答案漏答最大值

- 题目MMD第1033–1036行明确要求同时求最小值和最大值。
- 答案MMD第614–620行已计算 `f(-1)=e^3`、`f(1)=e^{-3}`、`f(0)=0`、`f(2/3)=4/(9e^2)`，但第624–626行只写出最小值为0，未写最大值结论。
- 独立比较得到：最小值为0（`x=0`），最大值为 `e^3`（`x=-1`）。
- `corrections[0].original` 已保留答案MMD第614–624行的逐字片段；由于没有原扫描页，`error_origin` 记为 `source_original`，只表示冻结来源本身呈现该问题，不推断转换环节。
- 判定：`answer_pairing=issue`、`answer_mathematics=needs_correction`、`correction_status=corrected_verified`、`record_status=audit_pending`。

### Q13：从基本原理求导的来源答案不完整

- 题目MMD第1121–1136行的(a)要求从基本原理求 `dy/dx`。
- 答案MMD第868–880行只列初始差商极限，随后为空白得分标记；第881行已直接进入(b)，没有化简和最终导数。
- 独立补全：
  `dy/dx = lim_{h→0}(1-1/[x(x+h)]) = 1-1/x^2`（`x≠0`）；由此(b)为 `x<-1` 或 `x>1`。
- `corrections[0].original` 已保留答案MMD第871–881行的逐字片段；由于没有原扫描页，`error_origin` 记为 `source_original`，不推断转换环节。
- Joy决策项：受控词表没有“从基本原理求导”或“切线斜率为正的取值区间”标签。本次保持 `tags=[]`；Joy须决定继续允许空标签，或在后续词表增补对应标签。该项已写入本题 `unresolved_issues`。
- 判定：`answer_pairing=issue`、`answer_mathematics=needs_correction`、`correction_status=corrected_verified`、`record_status=audit_pending`。

### Q16：导数阶数题答冲突，且拐点坐标漏结论

- 题目原始MMD英文第1178行和中文第1188行均写成(b)求 `f''(x)`。
- 答案MMD第991–999行的(b)实际计算 `f'(x)`；第1000行的(c)又明确写“By (b), we have `f'(x)=...`”。当前 `complete_questions_45.json` 已静默采用 `f'(x)`，但没有保留来源校订证据。
- 题答链和后续推理共同证明(b)应为求 `f'(x)`；审计结果保留原文、订正文、理由和精确MMD行号。
- 答案MMD第1013–1023行在(d)求出二阶导数并完成 `x=-5` 的变号表，却未写所求拐点坐标。独立代入得 `f(-5)=0`，故拐点为 `(-5,0)`。
- 三项 `corrections[].original` 均改为冻结MMD的逐字片段/原值；由于没有原扫描页，`error_origin` 记为 `source_original`，不把冲突或遗漏断言为Mathpix转换错误。
- 判定：`english_text=issue`、`chinese_text=revised`、`formula_symbols_units=issue`、`answer_pairing=issue`、`answer_mathematics=needs_correction`、`correction_status=corrected_verified`、`record_status=audit_pending`。

## 其他核对结论

- 17题题目边界均完整，未拆小问、未混入相邻题。
- 17题总分均能从题目MMD可靠读取，且与答案标示合计一致。
- 除Q16导数阶数外，英文原题的数值、变量和小问结构与冻结MMD一致；中文复核题干均已自然化而不改变数学信息。
- 除Q6、Q13、Q16所列问题外，其余14题的来源答案与独立复算一致。
- 未发现需要阻断使用的核心条件缺失；唯一未关闭项为Q13的受控标签词表决策，不影响数学订正结论。
- 审计没有修改 `complete_questions_45.json`、数据库、CSV、工作表或任何冻结来源。

## 自检命令

以下命令均以工作区 `/workspace/scratch/25757421d1d8` 为当前目录：

```bash
jq -e 'type=="array" and length==17' 'V1.16_complete_question_audit/derived/task3_review/review_甲部特训.json'

jq -e '([.[].question_id]|length)==([.[].question_id]|unique|length) and all(.[]; .source_section=="甲部特训")' 'V1.16_complete_question_audit/derived/task3_review/review_甲部特训.json'

jq -r 'group_by(.record_status)|map({status:.[0].record_status,count:length})' 'V1.16_complete_question_audit/derived/task3_review/review_甲部特训.json'

jq -e 'all(.[]; (.primary_type|IN("切线与法线","极值与曲线性质","最值与最优化","变率","综合微分应用")) and (.difficulty_level>=1 and .difficulty_level<=5) and ([.difficulty_dimensions[]]|all(.>=0 and .<=2)))' 'V1.16_complete_question_audit/derived/task3_review/review_甲部特训.json'

jq -e --slurpfile tax 'V1.16_complete_question_audit/derived/differentiation_application_taxonomy.json' 'all(.[]; all(.tags[]; IN($tax[0].tags[])))' 'V1.16_complete_question_audit/derived/task3_review/review_甲部特训.json'

jq -e 'all(.[]; has("question_id") and has("source_section") and has("checks") and has("question_text_zh_reviewed") and has("solution_verified") and has("answer_status_reviewed") and has("answer_verification_status") and has("primary_type") and has("tags") and has("difficulty_level") and has("difficulty_dimensions") and has("difficulty_evidence") and has("correction_status") and has("corrections") and has("duplicate_status") and has("duplicate_reference") and has("duplicate_evidence") and has("unresolved_issues") and has("audit_notes") and has("record_status"))' 'V1.16_complete_question_audit/derived/task3_review/review_甲部特训.json'

jq -e '([.[] | .corrections[] | select(.error_origin=="mathpix_conversion")]|length)==0 and (.[] | select(.question_id=="M2QD-DA-PARTA-Q13") | (.tags==[] and (.unresolved_issues|length)==1))' 'V1.16_complete_question_audit/derived/task3_review/review_甲部特训.json'
```

预期状态统计为：`audit_passed=14`、`audit_pending=3`、`blocked=0`。
