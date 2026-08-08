# Task 7: Codex 工程初始化设计

## 范围

Task 7 只建立 Joy M2 AI Database 的 Git 工程外壳与冻结基线，不迁移或重写 Task 5/6 数据流水线，不修改 497 道正式题，不开发 App、API、组卷器或新题功能。

## 仓库边界

新仓库位于 `joy-m2-ai-database/`。原工作区根目录的 `.git` 是系统占位目录，不是有效仓库，因此不在原位初始化。旧 `task4_work/`、`task5_work/`、`task6_work/` 与 `outputs/` 保持原样，新仓库只复制可独立复验所需的最小内容。

## 目录设计

```text
joy-m2-ai-database/
├── AGENTS.md
├── PROJECT_CONTEXT.md
├── PROJECT_STATE.md
├── README.md
├── pyproject.toml
├── .gitignore
├── src/joy_m2/
│   ├── audit/
│   ├── db/
│   ├── export/
│   └── release/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── regression/
├── data/
│   ├── raw/
│   ├── baselines/V1.18/
│   └── staging/
├── releases/V1.18/
├── legacy/
│   ├── task4_work/
│   ├── task5_work/
│   ├── task6_work/
│   └── outputs/25757421d1d8/Task5_V1.17_正式入库/
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── reports/
│   └── superpowers/
└── scripts/
```

`src/joy_m2/` 在 Task 7 中只建立包边界，不接管现有流水线。`legacy/` 是临时兼容区，仅保存运行 Task 3–6 共 54 项回归所需的最小快照；Codex 日常不得默认扫描该目录。Task 8 才会把可执行逻辑逐步迁移到 `src/joy_m2/`。

## V1.18 冻结方法

1. 将 V1.18 正式发布目录逐字节复制到 `releases/V1.18/`。
2. 在 `data/baselines/V1.18/BASELINE_LOCK.json` 固定版本、题量、答案分布、正式数据库 SHA-256、`SHA256SUMS.txt` SHA-256 与原始正式 ZIP SHA-256。
3. 新增只读回归测试：先验证锁文件中的固定值，再运行发布包内置验证器，检查 `PASS`、497/452/45 题计数、CSV 与 Markdown 覆盖。
4. Git 负责内容历史与回滚；文件权限只作为本地辅助保护，不作为唯一冻结机制。

固定摘要：

- `SHA256SUMS.txt`: `ae7fea3558a8942262ab8578a66d9d4c3330fe0c9683de9aeaedac462bb750f3`
- V1.18 SQLite: `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`
- 原始正式 ZIP: `302782a47f347ce2b75a7813903f5d0b4c29fae2e0a837ccdc98b7b3439b4d4e`

## Git 与隐私

仓库使用 `main` 作为基线分支，Task 7 实现在 `task7/codex-engineering-init` 分支完成。仓库不配置公共远端，不包含密码、API Key、令牌或私钥；是否连接私有 GitHub 远端由 Joy 在本地验收后另行决定。

`.gitignore` 排除虚拟环境、缓存、临时数据库、暂存输出、本地秘密文件与 Codex worktree 目录。正式 V1.18 发布资产和基线锁文件必须被 Git 跟踪。

## 测试与错误处理

Task 7 验收分三层：

1. 工程结构测试：项目入口、标准目录、Python 包边界与只读基线路径存在。
2. V1.18 冻结测试：固定摘要、内置验证器、数据库计数与答案分布不变。
3. 历史回归：从 `legacy/` 运行 Task 6×22、Task 5×10、Task 3×13、Task 4×9，共 54 项。

任一摘要、SQLite 完整性、外键、题量、答案状态或历史回归失败，Task 7 不得标记完成。不能通过更新固定哈希、降低断言或跳过测试来消除失败。

## 不可改变行为

- V1.18 的 497 道题及其稳定 ID、题目边界、原题、中文题干、答案身份、难度、标签、图片、校订和可抽取状态保持不变。
- 一道完整题一条记录，题内小问不拆分、不单独抽取。
- SQLite 继续是唯一正式事实源；CSV、Markdown 与报告继续是派生物。
- `missing_from_source` 的 34 题保持空答案但可供学生版使用；71 题独立复核答案不得冒充官方答案。
- Joy 明确审批前不写入正式 SQLite/CSV，不提升正式版本。
- Task 7 不实现统一 CLI，不重构 `build_task5_release.py` 或 `build_task6_release.py`。

## 验收结果

完成时应具备：有效本地 Git 仓库、标准目录、精简 `AGENTS.md`、准确项目文档、Python 3.12 工程元数据、V1.18 冻结锁、可独立运行的 Task 7 测试，以及 54 项历史回归和正式包验证的全新通过证据。
