# “应试训练”14题逐题复核报告

## 结论

- 复核题数：14
- `audit_passed`：0
- `audit_pending`：14
- `blocked`：0
- 数学答案：13题直接通过；Q7来源答案推导正确但漏写最终拐点结论，已独立补全并复核。

14题全部列为待修的共同原因，是 `complete_questions_45.json` 把答案来源错误映射到题目档 `M2Quick Drill-微分法的应用.mmd.zip / ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`，并沿用该错误成员的SHA-256 `4b963982fc5f5b0c4efc94ab64c76b6421c8f0389e7025f110783799b2c1fac5`。逐题核查确认，实际出版社答案均在 `微分的应用甲部.mmd.zip / c2e97ff4-9258-43ff-802f-ac95d2c5c0e2.mmd` 第5–448行，正确成员SHA-256为 `bfd75702b5abff3f604bfeb722f6ab7cd6c23566d15ea550bbf05be1b4dbbeb0`。文件、成员及成员哈希三者的来源追溯问题均已在每题 `corrections` 与 `unresolved_issues` 中保留证据。

## 核对方法

1. 以 `review_contract.md` 为唯一输出字段契约，逐条核对14个完整题记录，不拆小问。
2. 将题面记录与题目 MMD 第410–991行逐题比对，检查英文、中文、公式、符号、单位、小问、总分和题界。
3. 将来源答案与甲部答案 MMD 第5–448行逐题比对，并直接解压计算答案成员SHA-256；对Q11、Q12另查看出版社曲线图原图，确认文字转录与分支形状、极值及渐近线一致。
4. 独立重算每题的导数、驻点／拐点、渐近线、端点比较或相关变化率，并检查特殊分母、定义域、变号、漏出负号及单位。
5. 只使用受控主类型和标签，并按整题最高稳定认知要求给出Joy Level及六维0–2评分。
6. 对与同批或历史题的关系逐题复核；同函数但不同要求的Q3/Q7记为改编关系，不视为整题重复。

## 发现的问题与证据

| 范围 | 状态 | 问题 | 证据／处理 |
|---|---|---|---|
| Q1–Q14 | 待修 | 14题答案来源文件、成员及成员SHA-256全部映射错误 | 题目档MMD只有题面；答案实际见甲部答案MMD第5–448行。每题已给出正确档名、成员名、行号，并把成员哈希由 `4b963…` 校订为实算的 `bfd757…`。 |
| Q3 | 待修 | `marks_total` 为 `null` | 甲部答案MMD第106、108、117、125行合计4分，第126行明确为（4）；建议改为4。数学答案未改，`answer_verification_status` 为 `checked_pass`。 |
| Q7 | 待修 | `marks_total` 为 `null`，且来源答案漏写最终坐标结论 | 甲部答案MMD第228–258行合计并标示6分；独立复算确认拐点为 $(-1,0)$、$(1,0)$。 |
| Q13 | 待修 | `marks_total` 为 `null` | 甲部答案MMD第392、402、403行合计3分，第404行明确为（3）；建议改为3。数学答案未改，`answer_verification_status` 为 `checked_pass`。 |
| Q8 | 已核实校订 | 原出版社答案在求根后连续出现两个`1M`，可见分值合计7而题面总分为6 | 甲部答案MMD第285–286行；保留一个`1M`后(a)3分、(b)3分。输入答案已采用正确版本，本报告补回校订证据。 |
| Q11 | 已核实校订 | 中文正负号说明在原始MMD中遭OCR破坏 | 题目MMD第871行；依据英文第855行及表格第849–854行恢复。 |
| Q12 | 已核实校订 | 中文正负号说明被OCR误识为LaTeX括号／希腊字母 | 题目MMD第905行；依据英文第889行及表格第883–888行恢复。 |

没有发现阻断性题界缺失、关键题面图片缺失或无法复算的核心条件。Q11、Q12题目本身不依赖图片；其作图答案已与提取的出版社原图逐一核对。

## 分类与难度摘要

- 主类型分布：切线与法线2题、极值与曲线性质8题、最值与最优化2题、变率2题。
- Joy Level分布：Level 2共3题，Level 3共7题，Level 4共4题，Level 1及5均为0题。
- 所有标签均来自 `differentiation_application_taxonomy.json`；没有因答案顺带采用某方法而添加非题目能力标签。

## 自检命令

```bash
jq empty V1.16_complete_question_audit/derived/task3_review/review_应试训练.json

jq -e 'length == 14 and ([.[].question_id] | unique | length) == 14 and all(.[]; .source_section == "应试训练")' \
  V1.16_complete_question_audit/derived/task3_review/review_应试训练.json

jq -e --slurpfile tax V1.16_complete_question_audit/derived/differentiation_application_taxonomy.json '
  all(.[];
    (.primary_type as $p | $tax[0].primary_types | index($p) != null) and
    (all(.tags[]; . as $t | $tax[0].tags | index($t) != null)) and
    (.difficulty_level >= 1 and .difficulty_level <= 5) and
    (all(.difficulty_dimensions[]; . >= 0 and . <= 2))
  )' V1.16_complete_question_audit/derived/task3_review/review_应试训练.json

jq -e 'all(.[];
  (.checks.question_boundary | IN("pass","issue")) and
  (.checks.english_text | IN("pass","issue")) and
  (.checks.chinese_text | IN("pass","revised","issue")) and
  (.checks.formula_symbols_units | IN("pass","issue")) and
  (.checks.subparts_and_marks | IN("pass","unknown","issue")) and
  (.checks.necessary_images | IN("pass","not_required","issue")) and
  (.checks.answer_pairing | IN("pass","missing","issue")) and
  (.checks.answer_mathematics | IN("pass","needs_correction","blocked"))
)' V1.16_complete_question_audit/derived/task3_review/review_应试训练.json

jq -e '
  ([.[] | .corrections[] | select(
    .field == "solution_source_member_sha256" and
    .error_origin == "database_mapping" and
    .original == "4b963982fc5f5b0c4efc94ab64c76b6421c8f0389e7025f110783799b2c1fac5" and
    .corrected == "bfd75702b5abff3f604bfeb722f6ab7cd6c23566d15ea550bbf05be1b4dbbeb0"
  )] | length) == 14 and
  ([.[] | select(.question_id == "M2QD-DA-TRAIN-Q3" or .question_id == "M2QD-DA-TRAIN-Q13") | .answer_verification_status] | all(. == "checked_pass")) and
  ([.[] | select(.question_id == "M2QD-DA-TRAIN-Q7") | .answer_verification_status] == ["corrected_verified"])
' V1.16_complete_question_audit/derived/task3_review/review_应试训练.json

sha256sum \
  'V1.16_complete_question_audit/frozen_sources/M2Quick Drill-微分法的应用.mmd.zip' \
  'V1.16_complete_question_audit/frozen_sources/微分的应用甲部.mmd.zip'

unzip -p 'V1.16_complete_question_audit/frozen_sources/微分的应用甲部.mmd.zip' \
  'c2e97ff4-9258-43ff-802f-ac95d2c5c0e2.mmd' | sha256sum
```

预期两个冻结来源档案哈希分别为 `c98efaa053499e260f72950f8c7067dbba2b641ad104375c0efaa65f116f0749` 与 `7306fcbcb9d2e2ff67d4ebc0c79ff38520dfe4a2d8f897b9556bdf62cde471b5`；甲部答案MMD成员哈希应为 `bfd75702b5abff3f604bfeb722f6ab7cd6c23566d15ea550bbf05be1b4dbbeb0`。
