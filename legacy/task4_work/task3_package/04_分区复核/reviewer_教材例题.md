# 教材例题 8 题独立复核报告（最终差分复核）

## Verdict

- **规格符合性 verdict：PASS_WITH_REVIEW。** 8 条记录的必填字段、枚举、受控主类型、标签词形及 Level 范围均合法；状态分布为 `audit_passed=5`、`audit_pending=3`、`blocked=0`。Q3、Q6、Q8 的待决/待修事项均已显式记录，符合无 P0、仍有 P1/P2 人工复核项的 `PASS_WITH_REVIEW` 边界。
- **审计质量 verdict：PASS。** 前次复核的 2 项 Important 均已闭环：Q3 删除了语义错误的 `区间最值` 标签，并将词表缺口作为未决事项；Q6 不再把原有 `<1` 判为错误，也不再无证据归因 Mathpix。未发现新的审计质量问题。

## 最终问题计数

以下计数指本轮独立复核仍发现的审计缺陷；原审计已正确登记的 Q3/Q6/Q8 待决来源事项不重复计为复核缺陷。

| 严重度 | 数量 |
|---|---:|
| Critical | 0 |
| Important | 0 |
| Minor | 0 |

## 前次 Important 关闭情况

### Q3 标签语义 — 已关闭

- `tags` 已由 `区间最值` 改为 `[]`；不再给全域全局最小值题套用区间最值标签。
- `unresolved_issues` 明确登记受控词表缺少“全局最值/全局最小值”标签。
- `record_status` 已改为 `audit_pending`，等待 Joy 决定扩词或接受空标签。
- 主类型 `最值与最优化`、Level 4、全局最小值 \(-1152\) 均保持正确。

该处理符合契约对 `audit_pending` 允许分类待审的边界，也符合“只标题目明确要求的能力”的规则。

### Q6 变率校订理由 — 已关闭

- 校订理由现已明确冻结 MMD 的 \(dA/dt<1\) 结论本身正确，只把
  \[
  0\le \frac{dA}{dt}\le \frac{e}{\sqrt{e^2+1}}<1
  \]
  作为补足推导及更紧的精确上界。
- `error_origin` 已改为 `source_original`；理由明确说明缺少原扫描页，不将 MMD 简略写法判为数学错误或归因 Mathpix。
- 英文 `$C . L$` 定界问题仍由冻结 MMD 第 1288–1289 行中英对照直接支持，因此 Q6 保持 `audit_pending` 合理。

## 最终逐题结论

| 题目 | 数学与证据 | 分类与 Level | 状态复核 | 最终结论 |
|---|---|---|---|---|
| Q1 | 切点 \(h=6\)、切线 \(3x-y-10=0\) 正确；MMD 第 364 行支持斜率式校订 | 一致，Level 3 | `audit_passed` 合理 | 通过 |
| Q2 | 极大点 \((-3,-3)\) 正确；来源无分值，`unknown` 合理 | 一致，Level 3 | `audit_passed` 合理 | 通过 |
| Q3 | 全局最小值 \(-1152\) 正确 | 空标签与词表缺口已如实记录，Level 4 | `audit_pending` 合理 | 通过（待词表决定） |
| Q4 | 两个拐点及漏印二阶导数校订均正确、有据 | 一致，Level 3 | `audit_passed` 合理 | 通过 |
| Q5 | 渐近线 \(x=-2\)、\(y=x+3\) 正确 | 一致，Level 2 | `audit_passed` 合理 | 通过 |
| Q6 | 法线、最大面积与变率推导正确；英文定界问题有据；上界校订理由已修正 | 一致，Level 5 | `audit_pending` 合理 | 通过（待英文回写） |
| Q7 | 面积变率 \(-2\) 正确；MMD 截断证据支持重建 | 一致，Level 4 | `audit_passed` 合理 | 通过 |
| Q8 | 切点处 \(G=L=0\)，其余点严格 \(G<L\)；订正有据 | 一致，Level 4 | `audit_pending` 合理 | 通过（待来源措辞决定） |

## 专项确认

- **Q6 英文定界：确认原审计判定正确。** `$C . L$` 应分成 `$C$. $L$`；在英文原题字段回写前保持 `english_text=issue`、`formula_symbols_units=issue` 和 `audit_pending`。
- **Q8 切点等号：确认原审计判定正确。** 严格凹性给出 \(G\le L\)，且只有切点 \(x=\pi\) 取等号；在来源措辞决策前保持 `answer_mathematics=needs_correction` 和 `audit_pending`。

## 哈希确认

已按 `pre_task_hashes.json` 重新核对 10 个受保护对象；全部字节数及 SHA-256 匹配，包括 6 个 SQLite/CSV、正式 V1.16 包及 3 个冻结 MMD ZIP。未发现受保护文件变更。
