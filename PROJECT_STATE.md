# Joy M2 AI Database — PROJECT_STATE

> 更新时间：2026-08-08（Asia/Shanghai）
> 当前正式数据版本：Joy DSE M2 题库 V1.18
> 当前工程状态：Task 7 已完成
> 正式黄金基线：`releases/V1.18/`

## 0. 当前结论

- 工程已初始化为 Git 仓库，默认分支为 `main`。
- 初始快照共31个路径已暂存；因当前 Git 未配置作者姓名和邮箱，尚未创建首次提交。
- `SHA256SUMS.txt` 列出的14个受保护文件及清单自身已完整隔离到 `releases/V1.18/`，文件内容及 SHA-256 均未改变。
- 已建立 `pyproject.toml`、`src/joy_m2/`、`tests/regression/`、根级 README、AGENTS 和项目上下文。
- Python 版本约束为 `>=3.12,<3.13`，基准版本3.12.13；运行时仅使用标准库。
- 统一验证入口为 `python -m joy_m2 verify-baseline`。
- 统一测试入口为 `python -m unittest discover -s tests -v`。

## 1. 正式数据状态

- 完整题 V2 层：497道；V1.17 原45道，Task 6新增452道。
- 答案：392题 `source_provided`、71题 `ai_solved_verified`、34题 `missing_from_source`。
- 难度：L1×11、L2×54、L3×140、L4×190、L5×102。
- V1.16 历史兼容层：1,517条题目记录、24个来源、12个专题。
- 图片引用34项；结构化校订59项；精确重复0。
- SQLite `user_version=118`、`integrity_check=ok`、外键异常0。
- CSV为497行并与 SQLite 逐列逐值一致；Markdown包含497题及34个真实缺答案状态。

## 2. Task 7 交付

1. 初始化 Git `main` 分支。
2. 将自包含正式包移动到 `releases/V1.18/`，通过原生验证器恢复严格文件集合验证。
3. 创建标准 `src` 布局和 `joy-m2` 命令入口。
4. 创建 V1.18 基线回归测试，覆盖哈希、SQLite、CSV、Markdown、审计及核心业务分布。
5. 创建 `pyproject.toml`、`.python-version`、`.gitignore` 和 `.gitattributes`。
6. 建立根级 `AGENTS.md`、`README.md`、`PROJECT_CONTEXT.md` 和本状态文件。
7. 保留正式包内原始 `PROJECT_STATE.md`，根级状态独立维护。

## 3. 基线验证记录

使用 Python 3.12.13 验证：

- V1.18 原生验证器：`PASS`。
- 新基线 CLI：`PASS`，18项检查全部为 `true`。
- 根级回归测试：2/2通过。
- 正式题数量与唯一 ID：497/497。
- 可抽取完整题：497。
- V1.18 正式包全部受保护文件哈希与 `SHA256SUMS.txt` 一致。

## 4. 不变的核心决策

1. 一道完整题是一条记录；不拆分或单独调用小问。
2. SQLite 是唯一正式事实源；CSV和Markdown是受验证的派生层。
3. 原题、中文题干、答案身份、难度、类型、标签、来源、图片及校订轨迹不得静默改变。
4. `missing_from_source` 不得在无新证据和复核记录时改为已验证答案。
5. 新消费者只读取 `selectable_complete_questions_v2`；验证完成前保留历史兼容层。
6. `releases/V1.18/` 是只读黄金基线；任何未来数据变化必须另立版本和 migration。

## 5. 标准命令

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m joy_m2 verify-baseline
python releases/V1.18/verify_task6_release.py releases/V1.18
```

## 6. 已知边界与下一步

- 当前仓库不包含 V1.17 及更早完整输入工作区；正式包中的历史构建脚本属于冻结证据，不是当前完整重建入口。
- 组卷器、学生版和教师版尚未在本仓库完成消费者端到端验证，不能删除旧兼容层。
- 34道 `missing_from_source` 题目的答案补全必须另立任务，Task 7 未修改这些数据。
- 若未来补回原始 Mathpix ZIP，应另开来源再验证任务，不覆盖现有哈希轨迹。

## 7. 保护规则

- 禁止编辑、删除、重新格式化或替换 `releases/V1.18/` 内任何文件。
- 禁止修改497道正式题和任何业务数据。
- 禁止通过修改 manifest、哈希或降低断言绕过失败验证。
- 修改工程代码或文档前后都必须运行黄金基线验证。
