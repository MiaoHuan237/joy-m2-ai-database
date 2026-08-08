# Task 7 Codex Engineering Initialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可由 Codex 低 Token 长期维护的私有本地 Git 工程，同时逐字节冻结 V1.18，并保留 54 项历史回归能力。

**Architecture:** 新仓库使用标准 `src/tests/data/releases/docs/scripts` 边界；正式 V1.18 位于 `releases/V1.18`，独立锁文件与回归测试共同防止漂移；当前流水线以最小 `legacy/` 快照保留，Task 7 不改其逻辑。

**Tech Stack:** Git、Python 3.12、标准库 `unittest`/`sqlite3`/`hashlib`/`json`、SQLite 3、Markdown、SHA-256。

## Global Constraints

- V1.18 是只读黄金基线，497 道正式题不得改写。
- 一道完整题一条记录，题内小问不拆分、不单独抽取。
- SQLite 是唯一正式事实源；CSV、Markdown 和报告只能由 SQLite 派生。
- Task 7 不迁移或修改 Task 5/6 流水线，不实现统一 CLI，不开始 Task 8。
- 不包含密码、API Key、访问令牌、私钥或个人登录信息。
- 正式包固定摘要必须保持：清单 `ae7fea3558a8942262ab8578a66d9d4c3330fe0c9683de9aeaedac462bb750f3`，SQLite `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`。

---

### Task 1: 建立失败的工程结构验收

**Files:**
- Create: `tests/regression/test_task7_project_initialization.py`

**Interfaces:**
- Consumes: 仓库根路径。
- Produces: 对入口文件、标准目录、基线锁和最小 legacy 快照的可执行契约。

- [ ] **Step 1: 写结构测试**

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class ProjectStructureTests(unittest.TestCase):
    def test_required_project_entries_exist(self):
        required = [
            "AGENTS.md", "PROJECT_CONTEXT.md", "PROJECT_STATE.md", "README.md",
            "pyproject.toml", "src/joy_m2", "tests/unit", "tests/integration",
            "data/raw", "data/baselines/V1.18", "data/staging", "releases/V1.18",
            "docs/architecture", "docs/decisions", "docs/reports", "scripts",
        ]
        self.assertEqual([item for item in required if not (ROOT / item).exists()], [])
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python -m unittest -v tests/regression/test_task7_project_initialization.py`

Expected: FAIL because `AGENTS.md` and the standard directories do not exist.

- [ ] **Step 3: 保持测试失败，进入 Task 2**

不创建工程文件；先增加冻结行为测试，使实现一次满足两个契约。

### Task 2: 建立失败的 V1.18 冻结验收

**Files:**
- Modify: `tests/regression/test_task7_project_initialization.py`

**Interfaces:**
- Consumes: `data/baselines/V1.18/BASELINE_LOCK.json`、`releases/V1.18/`。
- Produces: `verify_v118_release()` 的行为要求与固定 SHA-256 断言。

- [ ] **Step 1: 增加冻结测试**

测试必须硬编码两个不可变摘要，读取锁文件，动态加载 `releases/V1.18/verify_task6_release.py` 并断言：`status=PASS`、`question_count=497`、`task6_question_count=452`、`existing_v117_question_count=45`、`csv_row_count=497`、`markdown_question_count=497`。同时查询 SQLite，断言答案分布为 `392/71/34`，`integrity_check=ok`，外键异常 0。

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python -m unittest -v tests/regression/test_task7_project_initialization.py`

Expected: FAIL because `BASELINE_LOCK.json` and `releases/V1.18` do not exist.

### Task 3: 建立最小标准工程与文档入口

**Files:**
- Create: `AGENTS.md`
- Create: `README.md`
- Create: `PROJECT_STATE.md`
- Create: `PROJECT_CONTEXT.md`
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `src/joy_m2/__init__.py`
- Create: `src/joy_m2/audit/.gitkeep`
- Create: `src/joy_m2/db/.gitkeep`
- Create: `src/joy_m2/export/.gitkeep`
- Create: `src/joy_m2/release/.gitkeep`
- Create: `tests/unit/.gitkeep`
- Create: `tests/integration/.gitkeep`
- Create: `data/raw/README.md`
- Create: `data/staging/README.md`
- Create: `docs/architecture/README.md`
- Create: `docs/decisions/README.md`
- Create: `docs/reports/README.md`
- Create: `scripts/README.md`

**Interfaces:**
- Consumes: 已批准的 Task 7 设计与现有 `PROJECT_CONTEXT.md`。
- Produces: Codex 自动读取规则、项目入口、Python 包边界与目录职责。

- [ ] **Step 1: 创建标准目录和精简项目文件**

`AGENTS.md` 只保存每次任务必须加载的冻结约束、读取顺序、测试命令、禁止扫描/修改范围和完成标准。`PROJECT_STATE.md` 记录 V1.18、Task 7 状态和下一任务为 Task 8 规划；不得声称 Task 8 已开始。

- [ ] **Step 2: 配置 Python 工程**

`pyproject.toml` 使用 `requires-python = ">=3.12,<3.13"`，不增加运行时依赖，不声明尚不存在的 CLI。

- [ ] **Step 3: 配置忽略规则**

忽略 `.venv/`、`__pycache__/`、`*.pyc`、`.pytest_cache/`、`.coverage`、`data/staging/*`、本地 `.env*`、临时 SQLite 文件与 `.worktrees/`；明确保留 `data/staging/README.md`。

### Task 4: 复制并锁定 V1.18 与最小 legacy 回归快照

**Files:**
- Create: `releases/V1.18/*`
- Create: `data/baselines/V1.18/BASELINE_LOCK.json`
- Create: `legacy/task4_work/task3_package/*`
- Create: `legacy/task4_work/task4_package/*`
- Create: `legacy/task5_work/build_task5_release.py`
- Create: `legacy/task5_work/test_task5_import.py`
- Create: `legacy/task5_work/v116/m2_question_bank/data/m2_question_bank.sqlite3`
- Create: `legacy/task6_work/*`
- Create: `legacy/outputs/25757421d1d8/Task5_V1.17_正式入库/*`

**Interfaces:**
- Consumes: 原工作区冻结产物与历史测试。
- Produces: 新仓库内可独立运行的 54 项回归输入，不依赖原工作区路径。

- [ ] **Step 1: 逐字节复制正式发布目录**

Run: `cp -a ../outputs/25757421d1d8/Task6_V1.18_正式入库/. releases/V1.18/`

- [ ] **Step 2: 复制最小 legacy 快照**

仅复制 Task 3/4 package、Task 5 构建脚本/测试/旧 SQLite、Task 6 工作目录与 V1.17 正式目录；删除复制出来的 `__pycache__` 和 `*.pyc`。不复制 34 MB 原始 ZIP、32 MB 字体或其他重复临时产物。

- [ ] **Step 3: 写入冻结锁**

`BASELINE_LOCK.json` 固定：版本 V1.18、497/452/45、答案分布 392/71/34、清单摘要 `ae7fea3558a8942262ab8578a66d9d4c3330fe0c9683de9aeaedac462bb750f3`、SQLite 摘要 `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`、原始正式 ZIP 摘要 `302782a47f347ce2b75a7813903f5d0b4c29fae2e0a837ccdc98b7b3439b4d4e`。

- [ ] **Step 4: 运行 Task 7 测试并确认 GREEN**

Run: `python -m unittest -v tests/regression/test_task7_project_initialization.py`

Expected: all Task 7 tests PASS.

### Task 5: 运行历史回归并记录证据

**Files:**
- Create: `docs/reports/TASK7_VERIFICATION.md`
- Modify: `PROJECT_STATE.md`

**Interfaces:**
- Consumes: 新仓库 `legacy/` 快照与 `releases/V1.18/`。
- Produces: 可复核的 Task 7 验收报告。

- [ ] **Step 1: 运行正式包验证**

Run: `python releases/V1.18/verify_task6_release.py releases/V1.18`

Expected: JSON includes `"status": "PASS"` and 497/452/45 counts.

- [ ] **Step 2: 运行 Task 6 回归**

Run: `(cd legacy && python -m unittest -v task6_work/test_task6_migration.py)`

Expected: 22 tests PASS.

- [ ] **Step 3: 运行 Task 5 回归**

Run: `(cd legacy/task5_work && python -m unittest -v test_task5_import.py)`

Expected: 10 tests PASS.

- [ ] **Step 4: 运行 Task 3/4 回归**

Run: `(cd legacy && python -m unittest discover -v -s task4_work/task3_package/06_构建与测试 -p 'test_task3_review.py')`

Expected: 13 tests PASS.

Run: `(cd legacy && python -m unittest discover -v -s task4_work/task4_package/05_构建与测试 -p 'test_task4*.py')`

Expected: 9 tests PASS.

- [ ] **Step 5: 记录全新验收结果**

报告写明实际命令、运行日期、通过数量、正式包计数和任何非阻断环境说明；`PROJECT_STATE.md` 只在全部验证成功后将 Task 7 标记完成。

### Task 6: 安全与 Git 收尾

**Files:**
- Modify: `.gitignore` only if verification reveals an untracked transient class.

**Interfaces:**
- Consumes: 完整 Task 7 工作树。
- Produces: 无缓存、无敏感信息、可提交的 feature branch。

- [ ] **Step 1: 扫描缓存与疑似敏感信息**

Run: `find . -path ./.git -prune -o -type f \( -name '*.pyc' -o -name '.DS_Store' \) -print`

Expected: no output.

Run: `rg -n --hidden -g '!.git/**' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|api[_-]?key\s*[:=]|access[_-]?token\s*[:=]|password\s*[:=])' .`

Expected: no real credential; documentation-only forbidden-pattern wording is manually reviewed.

- [ ] **Step 2: 运行完整最终验证**

重新运行 Task 7 测试、V1.18 验证和四组 54 项回归；必须使用本次工作树的新输出。

- [ ] **Step 3: 提交 Task 7**

Run: `git add -A && git commit -m "chore: initialize Joy M2 Codex engineering project"`

Expected: clean `task7/codex-engineering-init` branch with no remote configured.
