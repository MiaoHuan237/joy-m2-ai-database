# Joy M2 AI Database — Codex 项目交接说明

> 更新时间：2026-08-08（Asia/Shanghai）
> 当前正式版本：V1.18
> 当前工程阶段：Task 7，Git 工程初始化
> 正式数据基线：`releases/V1.18/`

## 1. 接手顺序

1. 完整读取根级 `AGENTS.md`、`PROJECT_STATE.md` 和本文件。
2. 阅读 `README.md`。
3. 读取 `releases/V1.18/manifest.json` 与正式入库报告。
4. 使用 Python 3.12 运行：

   ```bash
   python -m joy_m2 verify-baseline
   python -m unittest discover -s tests -v
   python releases/V1.18/verify_task6_release.py releases/V1.18
   ```

事实优先级：最新根级 `PROJECT_STATE.md` > V1.18 正式 SQLite 与 `manifest.json` > 正式入库报告 > README。历史说明和临时工作副本不能覆盖 V1.18 正式事实。

## 2. 项目目标与范围

本项目属于 Joy Teacher AI，服务于香港 DSE Extended Mathematics Module 2（M2），与 M1 数据隔离。题库保存完整原题、独立中文题干、答案与答案身份、分值、年份、Joy Level、类型、标签、来源、图片和校订轨迹，为后续教学组卷提供可审计数据。

当前工程只负责：

- 保护和验证 V1.18 正式数据；
- 提供标准 Python 包、依赖声明、测试入口和项目说明；
- 为后续审计、迁移、导出和发布工程化提供稳定仓库边界。

当前不负责 App/API、新题生成、M1 数据、34道缺失答案补写或业务数据修订。

## 3. 正式数据状态

- V2 正式层共497道完整题，其中 V1.17 原45道、Task 6 新增452道。
- 答案状态：392题 `source_provided`、71题 `ai_solved_verified`、34题 `missing_from_source`。
- 难度分布：L1×11、L2×54、L3×140、L4×190、L5×102。
- 16个主类型、397个受控标签、3,574条题目—标签关联、59项结构化校订。
- V1.16 历史兼容层保留1,517条旧记录、24个来源和12个专题。
- SQLite `PRAGMA user_version=118`；完整性正常、外键异常0、精确重复0。
- 新消费者入口为 `selectable_complete_questions_v2`。

## 4. 不可改变的业务规则

1. 一道完整题是一条记录，全部小问保留在题内；禁止小问级正式记录或随机调用。
2. SQLite 是唯一正式事实源；CSV、Markdown和统计必须与 SQLite 一致。
3. 永久保留来源原题；中文题干独立保存，不伪造缺失英文原文。
4. 来源答案、独立复核答案和来源缺失答案必须明确区分。
5. `missing_from_source` 可用于学生版，但教师版必须显示真实答案状态。
6. Joy Level 1–5 是整题教学难度，不是 HKEAA 官方难度。
7. 原题订正、来源、图片和哈希必须留痕，不得静默覆盖。
8. V1.16 冻结事实层、V1.17 原45题及整个 V1.18 发布包均不得修改。
9. 消费者迁移完成前，不删除旧 `leaf / complete / both` 兼容层。
10. 未来正式数据变更必须使用新版本、迁移记录、审计报告和 Joy 审批。

## 5. 技术栈与结构

| 层 | 实现 |
|---|---|
| Python | 3.12.x，基准版本3.12.13 |
| 运行依赖 | 仅标准库 |
| 主数据 | SQLite 3 |
| 派生资产 | CSV（UTF-8 BOM）、JSON、Markdown |
| 测试 | `unittest` |
| 工程元数据 | `pyproject.toml` |

```text
<repo-root>/
├── AGENTS.md
├── PROJECT_CONTEXT.md
├── PROJECT_STATE.md
├── README.md
├── pyproject.toml
├── src/joy_m2/
│   ├── baseline.py
│   ├── cli.py
│   └── __main__.py
├── tests/regression/
│   └── test_v118_baseline.py
├── releases/V1.18/
│   ├── Joy_M2_Complete_Question_DB_V1_18.sqlite3
│   ├── manifest.json
│   ├── SHA256SUMS.txt
│   └── 其余正式发布资产
└── docs/superpowers/plans/
```

`releases/V1.18/` 必须保持 manifest 与 SHA-256 文件集合完全一致。根级说明文件不得放入该目录。

## 6. 当前验证契约

`joy_m2.baseline.verify_baseline()` 和 `python -m joy_m2 verify-baseline` 检查：

- 正式包文件集合、manifest 与逐文件 SHA-256；
- SQLite 完整性、外键、schema版本和正式题唯一性；
- 497/45/452题量、历史层数量、答案和难度分布；
- `selectable_complete_questions_v2` 只包含已发布、Joy批准且可抽取的完整题；
- CSV 与 SQLite 逐列逐值一致；
- Markdown 497题以及34个真实缺答案状态；
- 审计记录、59项校订和精确重复0。

验证器以 SQLite 只读 URI 打开正式数据库，不应产生 journal 或其他写入副本。

## 7. 已知边界

- 当前仓库来源于 V1.18 自包含正式发布包，不包含原 Task 3–6 完整工作区、V1.17 数据目录或缺失的原始 Mathpix ZIP。
- 发布包内 `build_task6_release.py` 和 `test_task6_migration.py` 是冻结证据；缺少历史输入时不能作为当前完整重建入口。
- 系统自带 `/usr/bin/python3` 可能仍是3.9，不能运行使用 `zip(..., strict=True)` 的验证代码；必须使用 Python 3.12。
- 组卷器、学生版和教师版尚未在本仓库实现消费者端到端验证；在此之前不得删除兼容层。

## 8. 后续变更流程

1. 先运行全部基线验证并确认 `PASS`。
2. 工程变化只能写入根目录、`src/`、`tests/` 或 `docs/`。
3. 候选数据必须写入独立 staging 目录，不得覆盖 `releases/V1.18/`。
4. 数据变化必须另立版本和 migration；失败时不得修改基线哈希或降低断言。
5. 修改后再次运行原生验证器、根级回归测试和哈希检查，并更新根级 `PROJECT_STATE.md`。
