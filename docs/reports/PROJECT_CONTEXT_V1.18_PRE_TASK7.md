# Joy M2 AI Database / M2出题系统 — Codex 项目交接说明

> 更新时间：2026-08-08（Asia/Singapore）<br>
> 当前正式版本：V1.18<br>
> 交接范围：工程化重构（目录、导入、审计、迁移、测试、发布），暂不开发 App/API 产品功能<br>
> 正式数据基线：`outputs/25757421d1d8/Task6_V1.18_正式入库/`

## Codex 接手时的读取顺序

1. 完整读取本文件。
2. 完整读取 `library_work/M2出题系统/PROJECT_STATE.md`。
3. 完整读取 `library_work/M2出题系统/README.md`。
4. 读取 `outputs/25757421d1d8/Task6_V1.18_正式入库/Joy_M2_V1.18_正式入库报告.md` 和同目录 `manifest.json`。
5. 运行第 6 节的正式包验证命令；验证通过后才开始重构。

事实优先级：最新 `PROJECT_STATE.md` > V1.18 正式 SQLite 与 `manifest.json` > 正式入库报告 > README > 历史 Task 目录。历史对话、临时工作副本和旧版说明不能覆盖 V1.18 正式事实。

## 1. 项目目标

本项目属于 Joy Teacher AI，服务于香港 DSE Extended Mathematics Module 2（M2），与 M1 数据隔离。目标是把教材、DSE 真题、练习册、Mathpix 转换资料和教师资料转成可审计、可检索、可重复构建的结构化完整题题库，并支持后续教学组卷。

核心目标：

- 保存完整英文原题、独立中文题干、答案/解析、分值、年份、Joy Level 1–5、主类型、细分标签、来源文件、原题号、图片与校订轨迹。
- 按章节、知识点、题型、难度、来源、年份和标签稳定检索完整题。
- 以 JoyMathBook V3 为默认 LaTeX 模板，后续输出学生版 Worksheet、教师版答案和 Overleaf ZIP。
- 保持数据来源、答案身份、公式、图片、哈希和人工校订可追溯、可复核。
- 长期支持 DSE 风格模拟题、个性化练习和学生错题分析；这些属于后续产品阶段，不是本次工程化重构范围。

本次重构采用“B：工程化重构”：统一正式仓库、目录、依赖、导入脚本、数据库迁移、自动审计、测试和版本发布流程。不要在本次重构中扩展 App、Web 服务、外部 API 或新题生成产品。

## 2. 技术栈与目录结构

### 2.1 当前技术栈

| 层 | 当前实现 | 说明 |
|---|---|---|
| 运行时 | Python 3.12.13 | Task 5/6 只使用 Python 标准库；代码至少依赖现代 Python 的 `pathlib`、`sqlite3`、`unittest` 等能力 |
| 主数据 | SQLite 3 | V1.18 `PRAGMA user_version=118`；SQLite 是唯一正式事实源 |
| 派生数据 | CSV（UTF-8 BOM）、JSON、Markdown | CSV 是 SQLite 的人工检查镜像；JSON 保存审计/契约/manifest；Markdown 用于知识文档和报告 |
| 构建与封包 | `hashlib`、`zipfile`、SHA-256 | 支持确定性 ZIP、manifest、逐文件哈希和独立解压验证 |
| 测试 | Python `unittest` | Task 3–6 当前可执行回归共 54 项 |
| 旧题库代码 | Python 包 `src/m2bank` | V1.16 解析、专题分类、构建和旧组卷逻辑，属于历史兼容层 |
| 历史工作簿 | Node.js ESM + ExcelJS | 仅 Task 4 审阅工作簿使用；当前没有 `package.json`，不是 V1.18 主发布链依赖 |
| 文档/公式 | Markdown、LaTeX | JoyMathBook V3 为后续正式教学输出模板 |

当前无服务端、Web 服务器、API 或后台进程；“启动项目”是读取状态、验证正式包并运行数据流水线。当前也没有密码、API Key 或外部服务凭据依赖。

### 2.2 当前实际目录

```text
<repo-root>/
├── PROJECT_CONTEXT.md                         # 本交接文件
├── docs/superpowers/
│   ├── specs/                                 # 已批准设计
│   └── plans/                                 # Task 4–6 实施计划
├── library_work/M2出题系统/
│   ├── README.md                              # V1.18 业务规则
│   └── PROJECT_STATE.md                       # 最新状态权威说明
├── outputs/25757421d1d8/
│   ├── Task5_V1.17_正式入库/                   # Task 6 的冻结输入基线
│   └── Task6_V1.18_正式入库/                   # 当前正式发布目录
├── task6_work/
│   ├── build_task6_release.py                 # V1.17→V1.18 审计、迁移、导出、封包
│   ├── verify_task6_release.py                # 正式包独立验证器
│   ├── test_task6_migration.py                # 22 项 Task 6 测试
│   ├── task6_contract.json
│   └── task6_decisions.json
├── task5_work/
│   ├── build_task5_release.py                 # V1.16→V1.17 迁移
│   ├── test_task5_import.py                   # 10 项 Task 5 回归
│   └── v116/m2_question_bank/                 # V1.16 代码、来源 Markdown、图片、旧库与测试
├── task4_work/                                # Task 3/4 审计与工作簿历史过程
├── task4_inputs/                              # 旧输入副本，不是最新状态来源
└── task5_inputs/                              # Task 5 输入资料
```

重要目录身份：

- 正式 V1.18 数据：`outputs/25757421d1d8/Task6_V1.18_正式入库/`。
- 最新项目状态：`library_work/M2出题系统/PROJECT_STATE.md`。
- 当前 V1.18 可执行代码：`task6_work/`。
- `task4_inputs/M2出题系统/` 仍是 V1.16/Task 4 旧状态，不能作为最新说明。
- 当前根目录虽存在 `.git` 占位目录，但不是可用 Git 仓库；`git status`/`git rev-parse` 当前失败。

### 2.3 V1.18 主要数据库对象

- 历史兼容：`sources`、`topics`、`questions`、`question_topics`、`complete_questions`、`selectable_questions`。
- V2 正式：`complete_questions_v2`、`complete_question_tags_v2`、`complete_question_corrections_v2`、`complete_question_taxonomy_v2`、`import_runs_v2`、`release_metadata_v2`。
- 新消费者入口：`selectable_complete_questions_v2`。

## 3. 已完成的功能

### 3.1 正式数据状态

- V1.18 完整题 V2 层已全量覆盖 497 道完整题；一道完整题一条记录，不拆分小问。
- V1.17 的 45 道微分应用题逐字段保留；Task 6 从 23 个来源新增迁移 452 道。
- V1.16 历史兼容层保留 1,517 条旧记录、24 个稳定来源和 12 个专题，不作为新组卷主数据源。
- 答案状态：392 题 `source_provided`、71 题 `ai_solved_verified`、34 题 `missing_from_source`。
- 难度分布：L1×11、L2×54、L3×140、L4×190、L5×102。
- 已建立 16 个主类型、397 个受控标签、3,574 条题目—标签关联、59 项结构化校订和 34 项图片引用。
- 审计结果：P0=0、P1=0、精确重复 0；SQLite 完整性正常、外键异常 0。

### 3.2 数据流水线

- 从 V1.17 冻结 SQLite 提取其余 452 道候选完整题。
- 按来源批次完成题目边界、题号、题干、公式、中文字段、答案状态、分值、图片、标签、难度、重复关系和来源追溯审计。
- 事务式迁移到 `complete_questions_v2`，保留 V1.16 历史表及 V1.17 原 45 题。
- 从最终 SQLite 反向生成 497 行 CSV、497 题 Markdown 知识文档、入库报告和 `PROJECT_STATE.md`，避免多事实源漂移。
- 生成逐题审计 JSON、批次审计报告、manifest、SHA-256 清单、确定性 ZIP 和独立验证器。
- V1.18 正式包可独立验证文件哈希、SQLite 完整性、题量、CSV 一致性、Markdown 覆盖和审计状态。

### 3.3 历史能力

- V1.16 已有来源解析、专题分类、旧模型 SQLite/CSV 构建和 Worksheet MVP。
- Task 3/4 已有微分应用审阅、审计决策和五工作表人工审核工作簿。
- 这些历史能力尚未全部整理成统一 V2 CLI；尤其组卷器尚未完成“只读 `selectable_complete_questions_v2`”的消费者验证。

## 4. 重要设计决定

1. **完整题粒度**：一道完整大题对应一条记录；`(a)(b)(i)(ii)` 全部保留在同一题内。禁止新增小问级独立记录或小问级随机调用。
2. **正式事实源**：SQLite 是唯一主数据源；CSV、Markdown、报告和统计必须从最终 SQLite 生成，不能各自维护。
3. **语言保存**：永久保留来源原题；英文原题不能被中文覆盖。来源本身为中文时保留中文原文，不虚构英文版本。中文题干独立保存并记录复核状态。
4. **答案身份**：来源答案、独立复核解答和来源缺失答案必须明确区分。`ai_solved_verified` 不得描述为官方或出版答案。
5. **缺答案政策**：`missing_from_source` 不阻止正式入库和学生版抽取；教师版必须显示真实状态，答案字段保持为空，禁止伪造来源答案。
6. **难度口径**：Level 1–5 是 Joy 教学难度，不是 HKEAA 官方难度；按整道题评定。
7. **类型和标签**：每题仅一个主类型，可有多个细分标签；标签必须是受控、单行、真实考法词项，不继承混入 Markdown 表格的旧脏标签。
8. **校订留痕**：不能静默修正来源。原文、订正内容、理由、证据和复核状态必须可追溯。
9. **来源追溯**：保留 `source_id`、来源文件/成员、原题号、页码、图片和 SHA-256。原始 ZIP 缺失时只能使用已冻结来源哈希和逐题片段哈希，不得伪造已重新读取原档。
10. **重复处理**：精确重复是阻断项；改编题可保留，但必须记录与原题的关系。完全重复题不得在同一套卷中重复抽取。
11. **审批门禁**：新批次必须先生成预检/审计结果；只有 `audit_passed`、`unresolved_issues=[]` 且 Joy 明确批准后，才可更新正式 SQLite、CSV 和版本号。
12. **兼容层策略**：V1.16 `leaf / complete / both` 旧层暂时保留。所有消费者迁移并验证前不得删除；新开发默认只读 `selectable_complete_questions_v2`。
13. **版本保护**：V1.16 冻结事实层、V1.17 原 45 题和 V1.18 正式发布资产均为只读基线。本次重构不得顺手更改题目内容、答案身份或正式数据。
14. **确定性发布**：同一冻结输入应产生确定性输出；正式包必须包含构建证据、manifest、SHA-256 清单和可独立运行的验证器。

## 5. 已知问题

### 5.1 工程结构问题

- 当前目录不是可用 Git 仓库，代码、输入、历史任务、中间产物和正式发布物分散在多个 `task*_work`/`outputs` 目录。
- 没有统一的 `src/`、`tests/`、`data/`、`releases/` 结构，也没有根级 `AGENTS.md`、`pyproject.toml`、锁文件、Makefile/任务入口或 CI。
- `build_task6_release.py` 当前是可导入函数集合，没有稳定 CLI；路径、版本、日期和哈希常量仍与 V1.18 耦合。
- 当前版本发布依赖多个历史相对路径；移动目录前必须先建立路径契约和回归基线。
- 历史 Task 4 工作簿脚本依赖 ExcelJS，但没有随当前工程保存 Node 依赖清单。

### 5.2 数据与可重建边界

- V1.16 交付包缺少若干原始 Mathpix ZIP，因此部分旧批次不能从最原始档案完整重跑；不得声称已恢复这些档案。
- Task 3 旧交付包缺少 `build_audit_package.py`，其 19 项旧基础测试不能从包内独立复跑；当前可执行的是 13 项 Task 3 审阅测试。
- 34 道题仍为 `missing_from_source`，需要独立答案补全与数学复核；补全前不能改变状态。
- 2026 真题 12 道使用 `ai_solved_verified` 非官方独立解答；Q8(a) 的断开定义域积分常数严谨性风险已保留在审计说明中。
- 旧兼容层仍含小问级和旧标签数据；V2 已清洗，但不能通过改写历史层“修复”旧记录。
- 组卷器、学生版和教师版尚未完成只读 `selectable_complete_questions_v2` 的端到端验证，因此不能删除旧视图。

## 6. 启动和测试命令

以下命令均从当前代码根目录执行。项目没有常驻服务。

### 6.1 接手与正式包健康检查

```bash
cd /path/to/M2出题系统
python --version
sed -n '1,260p' PROJECT_CONTEXT.md
sed -n '1,260p' 'library_work/M2出题系统/PROJECT_STATE.md'
sed -n '1,320p' 'library_work/M2出题系统/README.md'
python task6_work/verify_task6_release.py \
  'outputs/25757421d1d8/Task6_V1.18_正式入库'
```

期望：Python 为 3.12.x；验证器输出 `"status": "PASS"`、`question_count=497`、`task6_question_count=452`、`existing_v117_question_count=45`、`csv_row_count=497`、`markdown_question_count=497`。

### 6.2 主测试

```bash
python -m unittest -v task6_work/test_task6_migration.py
(cd task5_work && python -m unittest -v test_task5_import.py)
```

当前期望：Task 6 为 22/22，Task 5 为 10/10。

### 6.3 可执行历史回归

```bash
python -m unittest discover -v \
  -s task4_work/task3_package/06_构建与测试 \
  -p 'test_task3_review.py'

python -m unittest discover -v \
  -s task4_work/task4_package/05_构建与测试 \
  -p 'test_task4*.py'
```

当前期望：Task 3 为 13/13，Task 4 为 9/9。四组可执行回归合计 54/54。

### 6.4 旧 V1.16 构建入口（仅用于理解，不得写入正式版本）

```bash
cd task5_work/v116
python m2_question_bank/build.py \
  --source /path/to/complete-v116-source-archive \
  --output /tmp/joy-m2-v116-rebuild
```

当前工程并不包含完整的 `/path/to/complete-v116-source-archive`；在原始 Mathpix ZIP 补齐前，此命令不是正式验收入口。不要用现有 V1.13 或不完整来源覆盖 V1.18。

## 7. 本次重构目标与不可改变的行为

### 7.1 重构目标

在不改变 V1.18 业务数据和用户可见行为的前提下，建立单一、可用 Git 管理、可重复构建的 Codex 工程：

- 将根级 `README.md`、`PROJECT_STATE.md`、`PROJECT_CONTEXT.md` 和精简 `AGENTS.md` 设为稳定项目入口。
- 把运行代码收敛到包式 `src/joy_m2/`，把单元、集成、回归和发布测试收敛到 `tests/`。
- 把来源、只读基线、暂存候选、审计结果和正式发布物分层；禁止在构建中覆盖原始输入或正式版本。
- 建立 `pyproject.toml` 与明确 Python 版本；移除隐式环境依赖。若保留工作簿工具，单独建立受控 Node 依赖清单。
- 把版本号、时间、输入路径、冻结哈希和发布目录从脚本常量迁移到显式配置/manifest。
- 提供单一 CLI，例如 `joy-m2 audit`、`joy-m2 migrate`、`joy-m2 export`、`joy-m2 verify`、`joy-m2 release`；每一步可单独运行且默认写入临时/候选目录。
- 统一审计契约、数据库迁移、导出与发布代码，避免 Task 5/6 大段重复和版本特例继续累积。
- 建立 CI：至少运行 V2 契约、数据库完整性、CSV 精确镜像、正式包验证和受保护基线回归。
- 记录架构决策与数据库迁移；任何数据变更必须使用新版本和 migration，不得直接编辑正式 SQLite。

推荐目标结构：

```text
<repo-root>/
├── AGENTS.md
├── PROJECT_CONTEXT.md
├── PROJECT_STATE.md
├── README.md
├── pyproject.toml
├── src/joy_m2/
│   ├── audit/
│   ├── db/
│   ├── export/
│   ├── release/
│   └── cli.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── regression/
├── data/
│   ├── raw/                    # 只读、按来源和哈希归档
│   ├── baselines/              # V1.16/V1.17/V1.18 受保护基线
│   └── staging/                # 可重建候选，不纳入正式事实
├── releases/V1.18/             # 正式发布物与 manifest
├── docs/
│   ├── architecture/
│   ├── decisions/
│   └── reports/
└── scripts/                    # 仅薄封装或一次性迁移，核心逻辑留在 src
```

### 7.2 不可改变的行为

- 不改变 V1.18 正式 497 题的稳定 ID、题目边界、原题、中文审定题干、答案身份、难度、类型、标签、图片、校订或可抽取状态。
- 不拆分小问，不创建小问级新题，不允许组卷器抽取单独小问。
- 新组卷消费者必须只读取 `selectable_complete_questions_v2`；旧视图仅用于兼容和回归。
- SQLite 继续是唯一事实源；CSV/Markdown/报告继续由 SQLite 生成并验证一致。
- 缺答案题继续允许学生版调用；教师版继续显示真实答案状态。
- 不把 AI/独立复核答案冒充来源答案、出版答案或 HKEAA 官方评分方案。
- 不静默修正原题，不覆盖来源，不破坏任何 SHA-256 和校订轨迹。
- Joy 明确审批前，不把候选批次写入正式 SQLite/CSV，也不提升正式版本。
- 不修改 V1.16 冻结事实层、V1.17 原 45 题或现有 V1.18 正式包；重构输出先进入隔离候选目录。
- 消费者迁移和等价性验证完成前，不删除 `leaf / complete / both` 兼容层。
- 本次重构不新增 M1 数据、不开发 App/API、不生成新题、不补写 34 道缺失答案。

## 8. 验收标准

### 8.1 文档与仓库

- 工程成为有效 Git 仓库；临时文件、缓存、数据库写入副本和本地环境文件由 `.gitignore` 管理。
- 根目录有准确的 README、PROJECT_STATE、PROJECT_CONTEXT、AGENTS.md、依赖清单和单一 CLI 说明。
- 从全新 checkout 按文档命令可安装/启动、运行测试和构建候选，不依赖历史聊天或未说明的本机路径。
- 正式输入、候选输出和发布物边界明确；默认命令不能覆盖冻结基线或正式发布目录。

### 8.2 数据等价性

- V1.18 正式包本身保持只读且 `verify_task6_release.py` 返回 `PASS`。
- V2 层保持 497 个唯一 `question_id`；V1.17 原 45 题逐字段不变，Task 6 的 452 题逐字段不变。
- V1.16 四张历史表逻辑内容不变；`questions=1517`、`sources=24`、`topics=12`。
- `selectable_complete_questions_v2` 继续只返回已发布、已审批且 `selectable=1` 的完整题。
- 答案分布保持 392/71/34；难度分布保持 11/54/140/190/102；结构化校订保持 59 项；精确重复保持 0。
- SQLite `PRAGMA integrity_check` 为 `ok`，`PRAGMA foreign_key_check` 返回 0 行。
- CSV 为 497 行并与 SQLite 逐列逐值一致；Markdown 含 497 个唯一题号并明确展示 34 个缺答案状态。

### 8.3 流水线与测试

- Task 6 的 22 项、Task 5 的 10 项、Task 3 的 13 项、Task 4 的 9 项可执行回归全部通过；重构后可用新的等价测试替代，但不能减少覆盖的业务门禁。
- 同一冻结输入连续构建两次，正式数据与封包结果确定；manifest 和 SHA-256 清单覆盖全部受保护文件。
- 最终 ZIP 自包含，解压到独立目录后无需开发工作区即可完成哈希、SQLite、CSV、Markdown和审计验证。
- 至少有一项端到端测试证明组卷器、学生版和教师版只读取 `selectable_complete_questions_v2`，且不会返回小问级记录。
- 任何失败必须终止发布；不能通过忽略测试、改写基线哈希或降低断言来“通过”验收。

### 8.4 安全与交付

- 仓库、日志、文档、测试夹具和发布包中不包含密码、API Key、访问令牌、私钥或个人登录信息。
- 正式数据修改必须有新版本号、迁移记录、审计报告、Joy 审批记录和可回滚发布包。
- 重构完成前先提交“仅结构/代码变化”的审阅结果；不得把未授权的数据修订混入同一变更。
