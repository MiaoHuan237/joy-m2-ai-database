# 甲部特训17题独立审计复核

## 复核范围与结论

本报告仅复核 `source_section="甲部特训"` 的17条记录，输入为：

- `derived/complete_questions_45.json`
- `derived/task3_review/review_contract.md`
- `derived/完整题入库标准_V1.0.md`
- `derived/task3_review/review_甲部特训.json`
- `derived/task3_review/report_甲部特训.md`
- 冻结题目 MMD `M2Quick Drill-微分法的应用.mmd.zip`
- 冻结答案 MMD `微分的应用甲部.mmd.zip`

逐题检查了题目边界、英中题干、公式/符号/单位、分值、必要图片、题答配对、答案数学、主类型、受控标签、Level 与生命周期状态。17题数学复算未发现新的错误；Q6、Q13、Q16 的既有数学订正均成立。

| 判定维度 | verdict | 依据 |
|---|---|---|
| **规格符合性 verdict** | **PASS_WITH_REVIEW** | 无 P0/Critical 问题；Q13 的受控词表覆盖缺口已正确写入 `unresolved_issues` 并保持 `audit_pending`，仍待 Joy 作词表决策。 |
| **审计质量 verdict** | **PASS** | 原复核提出的两项 Important 已全部修正；17题题答数学、分类、Level、状态和校订证据未发现新的审计质量问题。 |

问题计数：**Critical 0，Important 0，Minor 0**。

## Critical（0）

未发现会导致题目不可可靠使用、答案数学错误未识别、记录错误放行为 `audit_passed`，或需要改判 `blocked` 的问题。

## Important（0）

原复核的两项 Important 均已关闭：

| 原发现 | 最新差分证据 | 复核结论 |
|---|---|---|
| Q13 空标签未显式登记为分类缺口 | `tags=[]` 保持不变；`unresolved_issues` 新增受控词表缺少对应标签及 Joy 决策要求；报告同步说明该阶段边界 | 已关闭；不硬贴不准确标签且保持 `audit_pending`，符合当前规格 |
| Q6/Q13/Q16 校订来源归因及原文证据不足 | 相关 `error_origin` 全部改为 `source_original`；`corrections[].original` 改为冻结 MMD 的逐字片段/原值；报告明确不推断 Mathpix 环节 | 已关闭；校订证据满足当前冻结来源可验证范围 |

## Minor（0）

未发现独立成立的轻微问题。中文规范化、分值、必要图片判断、主类型与 Level 均无须另列 Minor。

## 三道重点题复核

### Q6：来源答案漏答最大值

题目 MMD 第1033–1036行明确要求最小值和最大值。答案 MMD 第594–627行给出驻点及四个候选值，但只落出最小值结论。独立复算：

\[
f'(x)=e^{-3x}x(2-3x),\qquad x=0,\frac23,
\]

\[
f(-1)=e^3,\quad f(0)=0,\quad f\!\left(\frac23\right)=\frac4{9e^2},\quad f(1)=e^{-3}.
\]

所以最小值为 $0$（$x=0$），最大值为 $e^3$（$x=-1$）。现有 `answer_pairing=issue`、`answer_mathematics=needs_correction`、`answer_verification_status=corrected_verified` 与 `record_status=audit_pending` 均恰当。

### Q13：基本原理答案不完整与空标签

答案 MMD 第868–880行只保留初始差商及分值标记，第881行已进入(b)。完整推导为

\[
\frac{dy}{dx}
=\lim_{h\to0}\frac{\left(\frac1{x+h}+x+h\right)-\left(\frac1x+x\right)}h
=\lim_{h\to0}\left(1-\frac1{x(x+h)}\right)
=1-\frac1{x^2},\qquad x\ne0.
\]

因此切线斜率为正时 $x<-1$ 或 $x>1$。现有补答数学正确；`tags=[]` 的词表覆盖限制已写入 `unresolved_issues`，并由 `audit_pending` 正确承载，等待 Joy 决策。

### Q16：一/二阶导数题答冲突与拐点坐标

题目 MMD 第1178、1188行均写(b)求 $f''(x)$，答案 MMD 第991–1001行却求 $f'(x)$，且(c)明确写“By (b), we have $f'(x)=\cdots$”。从题答链判断，(b)应为求一阶导数。

复算得到

\[
f'(x)=\frac{(x+5)^2(x-16)}{(x-2)^3},\qquad
f''(x)=\frac{294(x+5)}{(x-2)^4}.
\]

$x=-5$ 处 $f'$ 不变号，故不是转向点；$x=16$ 为极小点，坐标为 $\left(16,\frac{189}{4}\right)$。二阶导数在 $x=-5$ 处由负变正，且 $f(-5)=0$，故唯一拐点为 $(-5,0)$。$x=2$ 不在定义域，不能成为拐点。现有订正数学、标签、Level 4 与 `audit_pending` 均恰当；逐字 MMD 证据与阶段性 `source_original` 归因均已补齐。

## 逐题复核表

| 题号 | 题干/答案数学 | 主类型与受控标签 | Level | 状态复核 |
|---|---|---|---:|---|
| Q1 | 隐函数切线斜率 $-1/3$，切线 $x+3y+4=0$，正确 | `切线与法线`；`已知切点求切线`、`隐函数求导`，恰当 | 2 | `audit_passed` 恰当 |
| Q2 | 两切点及两条平行切线均正确 | `切线与法线`；`与指定直线平行的切线`、`切点未知`，恰当 | 3 | `audit_passed` 恰当 |
| Q3 | 未知切点约束、$a=\pm1$ 及两切线均正确 | `切线与法线`；`过指定点的切线`、`切点未知`，恰当 | 4 | `audit_passed` 恰当 |
| Q4 | 唯一极大点 $\left(\frac{2\pi}{3},\frac{2\pi}{3}+\sqrt3\right)$，正确 | `极值与曲线性质`；`极大点`，恰当 | 2 | `audit_passed` 恰当 |
| Q5 | 唯一极小点 $(\ln2,1)$，正确 | `极值与曲线性质`；`极小点`，恰当 | 2 | `audit_passed` 恰当 |
| Q6 | 已正确补出最大值 $e^3$ | `最值与最优化`；`区间最值`、`端点比较`，恰当 | 3 | `audit_pending` 恰当 |
| Q7 | 最小值 $-1/(2e)$、最大值 $0$，正确 | `最值与最优化`；`区间最值`、`端点比较`，恰当 | 3 | `audit_passed` 恰当 |
| Q8 | $k=5$，二阶导数两根及变号结论正确 | `极值与曲线性质`；`拐点`，恰当 | 3 | `audit_passed` 恰当 |
| Q9 | 参数、斜渐近线及局部极值点均正确 | `极值与曲线性质`；`极大点`、`极小点`、`渐近线`，恰当 | 3 | `audit_passed` 恰当 |
| Q10 | 两转向点、拐点与区间草图描述正确 | `极值与曲线性质`；`极大点`、`极小点`、`拐点`、`曲线作图`，恰当 | 3 | `audit_passed` 恰当 |
| Q11 | 渐近线、递减性、无拐点及双支图像正确 | `极值与曲线性质`；`渐近线`、`拐点`、`曲线作图`，恰当 | 4 | `audit_passed` 恰当 |
| Q12 | 圆锥相似关系、面积/体积变率及单位正确 | `变率`；5个相关受控标签均与题目条件或明确所求相符 | 4 | `audit_passed` 恰当 |
| Q13 | 基本原理推导已正确补全；(b)范围正确 | `极值与曲线性质` 可接受；空标签词表缺口已显式登记 | 3 | `audit_pending` 恰当；Joy 决策项完整 |
| Q14 | $f'(x)=\frac34x+6$，斜率与极小点横坐标正确 | `极值与曲线性质`；`极小点`，恰当 | 2 | `audit_passed` 恰当 |
| Q15 | 单调性、$p=3$、切线及凹性论证正确 | `极值与曲线性质`；`切点未知`、`拐点`、`凹凸性`，恰当 | 4 | `audit_passed` 恰当 |
| Q16 | 已正确解决导数阶数冲突并补出拐点 $(-5,0)$ | `极值与曲线性质`；`渐近线`、`极小点`、`拐点`，恰当 | 4 | `audit_pending` 恰当 |
| Q17 | 切点参数化、距离/面积链式变率及 $0.221$ 均正确 | `综合微分应用`；5个受控标签与跨板块任务相符 | 4 | `audit_passed` 恰当 |

## 无法验证事项

现有冻结材料没有 Q6、Q13、Q16 的完整原版印刷页面，故仍不能判断缺字/错阶导数究竟始于原出版资料还是转换环节。最新审计已将 `source_original` 明确定义为“冻结来源呈现的问题”，并不再推断 Mathpix 环节；因此该限制是阶段边界，不构成当前审计质量问题。

## 受保护哈希确认

依据 `derived/task3_review/pre_task_hashes.json` 对10个受保护文件重新计算字节数与 SHA-256，结果为 **10/10 全部匹配，0项 `P0-NONMUTATION-001`**。

最终未发现需改变其余14题 `audit_passed` 状态、Q6/Q13/Q16 的 `audit_pending` 状态，或17题主类型/Level 的依据；复核问题计数归零。
