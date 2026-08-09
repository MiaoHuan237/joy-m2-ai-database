# Task 8A：统一数据流水线接口与行为锁定设计

## 1. 状态与目标

本规格记录 Task 8A brainstorming 已确认的设计。Task 8A 只梳理并锁定 legacy Task 5/6 的真实行为，定义未来 `src/joy_m2/audit/`、`src/joy_m2/db/`、`src/joy_m2/export/`、`src/joy_m2/release/` 的职责、公开接口、数据契约、错误边界、测试矩阵以及 Task 8B 的兼容与回滚策略。

本规格获 Joy 书面批准前，不生成实施计划；Task 8A 不迁移或重写生产代码。

设计完成标准：

1. 四个模块各有单一职责，依赖方向明确。
2. 模块间通过不可变标准库值对象传递数据。
3. staging 构建与正式提升严格分离。
4. SQLite、CSV、Markdown、JSON、SHA-256 和确定性 ZIP 的可观察行为可测试。
5. 所有关键失败都有稳定策略，正式目录不会因失败而出现部分发布。
6. Task 8B 可并行重放新旧流水线，并在不修改 V1.18 的前提下验证等价性和回退。

## 2. 接管基线与不可变范围

Task 8A 从以下远端状态开始：

- `origin/main`：`295c8ae38b5b22c6ba449d2af7562cb1516cca4c`
- 历史中包含：`e3c9f61eebb72beedaf0aaf845b525e690b7bffe`
- 分支：`task8a/pipeline-contracts`
- Task 7：7/7
- Task 3–6：54/54
- V1.18 独立验证：`PASS`

以下事实在 Task 8A 与 Task 8B 中均不得因代码重构而改变：

- `releases/V1.18/` 与 `data/baselines/V1.18/` 不得原地修改。
- 497 道题继续以一道完整题一条记录保存，不拆分小问。
- V1.17 原 45 题与 Task 6 的 452 题保持不变。
- 答案身份保持 392 `source_provided`、71 `ai_solved_verified`、34 `missing_from_source`。
- 稳定 ID、题目边界、来源文本、中文审定文本、答案、难度、主类型、标签、图片、校订、哈希和选择状态保持不变。
- compatibility tables/views 在所有消费者迁移并验证前继续存在。
- SQLite 继续是唯一正式事实源；CSV、Markdown、报告和统计都是派生物。

本阶段不新增第三方依赖，不实现 CLI，不开始 App/API、自动出题、M1、Task 8B 或 Task 8C，不合并到 `main`，不删除远端备份分支。

## 3. legacy Task 5/6 真实行为清单

### 3.1 Task 5：V1.16 到 V1.17

`legacy/task5_work/build_task5_release.py` 的真实行为如下：

1. 使用硬编码的 V1.16 SQLite、Task 4 JSON、taxonomy、版本、审批时间和冻结哈希。
2. 要求恰有 45 个唯一、`audit_passed` 且无未解决事项的记录，并在构建器内把它们改为 `published`、`approved_by_joy` 和可选择。
3. 校验 V1.16 SQLite SHA-256 后复制数据库，在复制品中创建 V2 表、taxonomy、import run、metadata、索引和 `selectable_complete_questions_v2`。
4. 保留 V1.16 历史表和旧完整题视图；设置 `PRAGMA user_version=117`。
5. 检查 SQLite integrity 和 foreign keys，随后执行 `VACUUM`。
6. 从最终 SQLite 的 `complete_questions_v2 ORDER BY question_id` 生成 UTF-8 BOM CSV。
7. 从最终 SQLite 生成 Markdown 知识文档、入库报告和项目状态。
8. 生成排序键、两空格缩进、末尾换行的 JSON 证据和 manifest。
9. 封包前生成 `SHA256SUMS.txt`；ZIP 使用固定时间、权限、顺序和 DEFLATE 级别 9。
10. `build_release()` 会创建目标目录，并递归清空目标目录中原有的全部内容。
11. 脚本入口使用硬编码输出路径；没有稳定 CLI 或统一配置。

### 3.2 Task 6：V1.17 到 V1.18

`legacy/task6_work/build_task6_release.py` 与独立 verifier 的真实行为如下：

1. 校验 V1.17 SQLite 固定哈希、manifest 锁定值、SQLite integrity、foreign keys、45 个 V2 题和 497 个 legacy 完整题。
2. 从 legacy `complete_questions`、`sources`、`topics` 和 `question_topics` 联表提取 23 个来源的 452 道候选，排除已在 V1.17 迁移的来源。
3. 按 `source_id, question_number, question_id` 排序，并要求 452 个唯一 ID。
4. 在同一函数中完成候选提取、字段转换、答案身份判断、2026 年分值和难度补录、标签清理、图片解析、来源片段哈希、重复检查和审计报告生成。
5. 452 道答案身份是 347 `source_provided`、71 `ai_solved_verified`、34 `missing_from_source`；V1.17 的 45 道均为 `source_provided`。
6. `missing_from_source` 保持空答案；2026 非官方独立答案保持 `ai_solved_verified`，不声明为官方答案。
7. 精确重复立即阻断；缺图片、字段不完整或非缺失状态却没有答案时立即抛 `ValueError`。
8. 审计阶段已写入 `approved_by_joy`，技术审计和正式批准没有接口边界。
9. 数据库构建复制 V1.17，插入 452 道题和标签，重建 taxonomy，更新 metadata/import run，并设置 `user_version=118`。
10. V1.17 原 45 道 V2 题、历史四表和 compatibility views 保留。
11. 事务提交后检查 integrity 和 foreign keys，再执行 `VACUUM`；构建失败时可能在目标路径留下部分文件。
12. CSV 由最终 SQLite 按 `question_id` 生成；Markdown 按 `source_order` 生成；审计 JSON 在数据库构建前写入。
13. `build_release()` 不清空输出目录；同名文件会被覆盖，其他旧文件会保留。
14. `package_release()` 会修改 release 目录，复制构建证据并生成 verification、manifest 和 SHA 清单；目录中的额外文件可能进入保护集合和 ZIP。
15. Task 6 ZIP 在单一发布根目录下按文件名排序，固定时间为 1980-01-01、权限为 `0644`、`create_system=3`、DEFLATE 级别 9。
16. 构建器没有脚本入口；独立 verifier 接受一个 release 目录参数，正常完成检查时返回结构化 PASS/FAIL 和退出码 0/1，参数错误返回 2。
17. 缺文件、坏 JSON、坏 SHA 清单或 SQLite 无法打开时通常传播原生异常，而不是返回结构化 FAIL。

### 3.3 必须保留与必须纠正的边界

题目、答案身份、数据库逻辑、导出字节格式、文件集合、哈希关系和确定性封包属于必须锁定的行为。清空或混合输出、静默覆盖、审计与批准耦合、硬编码路径、部分写入和无统一异常属于已记录的 legacy 风险；新接口必须通过明确契约纠正这些风险，而不是把它们升级为未来规范。

## 4. 方案比较与选择

### 4.1 方案 A：契约优先的四模块流水线，已选择

- `audit` 负责候选审计并输出类型化结果。
- `db` 只把已通过的审计批次迁移为候选 SQLite。
- `export` 只从最终 SQLite 生成派生产物。
- `release` 负责安全编排、验证、封包和提升。
- 少量共享配置、值对象和异常放在 `joy_m2` 顶层，避免模块循环依赖。

优点是职责清楚、单元可独立测试、可分层迁移并保留回退路径。代价是 Task 8B 开始前必须先落实类型和契约。

### 4.2 方案 B：legacy 适配层，未选择

新模块只包装 Task 5/6 现有函数。迁移速度较快，但硬编码、路径破坏性、异常混乱和版本耦合会穿透新接口，之后仍需二次设计。

### 4.3 方案 C：通用步骤图，未选择

把全部阶段建模为可注册步骤和依赖图。扩展性较高，但当前只有一条明确流水线，会引入不必要的抽象、配置和测试复杂度。

## 5. 模块职责与依赖方向

数据流固定为：

```text
PipelineConfig
      ↓
audit → AuditResult / AuditedBatch
      ↓
db → DatabaseArtifact
      ↓
export → DerivedArtifacts
      ↓
release → CandidateRelease → VerificationReport → FormalRelease
```

`release` 是唯一高层编排者；`audit`、`db` 和 `export` 互不调用。未来 CLI 可以分别调用低层接口，但不能复制业务逻辑。

### 5.1 `joy_m2.audit`

单一职责是读取候选和审计契约，检查完整题边界、字段完整性、答案身份、来源追踪、图片、标签、难度、校订和重复关系，并汇总结构化 issues。

它不修改 SQLite，不生成 CSV/Markdown，不决定正式发布，也不写 `releases/`。技术审计通过只产生 `AuditedBatch`，不等于 Joy 正式批准。

### 5.2 `joy_m2.db`

单一职责是验证基线身份，并把 `AuditedBatch` 事务式应用到候选 SQLite。它负责 schema、metadata、import run、`user_version`、兼容对象保留、integrity 和 foreign-key 检查。

它不重新解释审计规则，不生成派生文件、manifest 或 ZIP。

### 5.3 `joy_m2.export`

单一职责是只读最终候选 SQLite，并生成 CSV、Markdown、入库报告和其他由 `ExportContract` 明确列出的派生产物。

它不迁移数据库，不修改题目，不判断发布目标，也不写正式目录。

### 5.4 `joy_m2.release`

单一职责是编排流水线与发布安全：创建隔离 staging run、持久化审计证据、调用数据库和导出阶段、生成 manifest/SHA/ZIP、独立验证候选，以及在明确审批后原子提升。

`build_candidate()` 永远只写 staging；`promote_candidate()` 是唯一允许写入 `releases/` 的接口。

### 5.5 共享文件

为避免四模块互相依赖，顶层只增加以下小型共享文件：

- `config.py`：`PipelineConfig` 与路径边界。
- `models.py`：不可变 dataclass 值对象。
- `errors.py`：领域异常层级。

共享文件不包含流水线编排或版本特例。

## 6. 配置与类型化数据传递

所有跨模块值对象使用标准库 `@dataclass(frozen=True)`。集合使用 tuple，路径使用解析后的绝对 `Path`。题目模型显式声明当前契约字段，不接受未约束的附加字典作为公共接口。

核心配置和值对象：

```python
PipelineConfig(repo_root: Path)

ReleaseSpec(
    release_version: str,
    baseline_version: str,
    baseline_sqlite_sha256: str,
    schema_version: str,
    created_at: str,
)

ApprovalRecord(
    release_version: str,
    candidate_manifest_sha256: str,
    approved_by: str,
    approved_at: str,
    scope: str,
)
```

`PipelineConfig` 从显式 `repo_root` 派生 `staging_root`、`releases_root` 和 `baselines_root`。库函数不自动寻找仓库、不读取当前工作目录、不读取环境变量。未来 CLI 可以发现仓库根目录，但必须显式构造 `PipelineConfig`。

`ReleaseSpec` 的时间、版本和哈希由调用方显式提供，核心逻辑不读取系统时钟。`ApprovalRecord` 必须绑定候选 manifest SHA-256，`approved_by` 必须是 `Joy`，版本和审批范围必须与候选一致。

代表文件的 `ArtifactRef` 至少包含绝对路径、SHA-256、字节数和 artifact kind。`CandidateRelease` 记录 run ID、版本、候选 manifest 哈希、验证报告、完整文件集合和候选 ZIP。`FormalRelease` 记录不可覆盖的正式目录、正式 manifest、验证报告和最终哈希。

JSON 是持久化审计与发布证据，不是进程内主要数据总线。

## 7. 公开 Python 接口

### 7.1 audit

```python
audit_batch(request: AuditRequest) -> AuditResult
AuditResult.require_passed() -> AuditedBatch
```

`AuditRequest` 包含来源 SQLite、资源根目录、`AuditContract`、已审核的版本决议和候选选择范围。`AuditResult` 包含全部记录结果、issues、统计和整体状态。存在 blocker 时，`require_passed()` 抛 `AuditBlockedError`。

### 7.2 db

```python
build_database(request: DatabaseBuildRequest) -> DatabaseArtifact
verify_database(path: Path, contract: DatabaseContract) -> VerificationReport
```

`DatabaseBuildRequest` 只接受 `AuditedBatch`、冻结基线、当前 staging run 内的目标路径、`ReleaseSpec` 和 `DatabaseContract`。

### 7.3 export

```python
export_database(request: ExportRequest) -> DerivedArtifacts
verify_exports(request: ExportVerificationRequest) -> VerificationReport
```

`ExportRequest` 只接受已完成的 `DatabaseArtifact`、当前 staging run 和 `ExportContract`。`DerivedArtifacts` 显式列出每个产物，不返回无约束路径字典。

### 7.4 release

```python
build_candidate(request: CandidateBuildRequest) -> CandidateRelease
verify_candidate(candidate: CandidateRelease) -> VerificationReport
verify_release(release_dir: Path, contract: ReleaseContract) -> VerificationReport
promote_candidate(
    candidate: CandidateRelease,
    approval: ApprovalRecord,
    config: PipelineConfig,
) -> FormalRelease
```

`CandidateBuildRequest` 包含配置、run ID、`ReleaseSpec`、audit/db/export/release contracts 和所需输入。高层构建顺序固定，但每个低层阶段仍可单独测试。

## 8. staging 与正式发布边界

### 8.1 候选构建

每次构建使用新的 `data/staging/<run_id>/`，run ID 由调用方显式提供。目标必须不存在。实际构建先发生在同一 staging 文件系统内的隐藏临时目录，全部阶段成功并通过独立验证后才原子改名为 run 目录。

失败构建不得出现为有效候选。需要保留诊断时，只能移动到 `data/staging/.failed/<run_id>/`，并写入明确的失败状态；该目录不含正式发布标记，也不能传给 `promote_candidate()`。

任何同名 staging run、ZIP 或其他声明输出已存在时均抛 `OutputConflictError`。不提供隐式清空、覆盖或 `replace=True`。

### 8.2 正式提升

正式提升采用两阶段模型：

1. 对候选执行一次新鲜的完整验证。
2. 校验 `ApprovalRecord` 的版本、候选 manifest SHA-256、审批人、时间和范围。
3. 确认 `releases/<version>/` 不存在。
4. 在 `releases/` 内部的临时目录复制已批准候选 payload。
5. 加入审批证据；正式 manifest 同时记录候选 manifest SHA-256 和审批证据 SHA-256，再生成正式 SHA 清单并重新独立验证。
6. 生成并验证由 `ReleaseContract` 规定的确定性 ZIP；ZIP 包含正式 manifest、SHA 清单与审批证据，但不进入自身的哈希闭包，其摘要由 `FormalRelease` 和后续 baseline lock 记录。
7. 使用同文件系统原子改名发布正式目录。

任一步失败均不得出现正式目标目录。正式 release 一旦存在便不可覆盖、原地回滚、原地修补或由流水线删除。

## 9. 数据与确定性契约

### 9.1 SQLite

- 打开数据库前校验冻结基线 SHA-256、版本和 manifest 绑定。
- 把基线复制到 staging 临时路径，再启用 foreign keys 并使用单次迁移事务。
- 保留全部 compatibility tables/views；Task 8B 不删除或重建为不同语义。
- 显式写入 schema、release metadata、import run 和 `PRAGMA user_version`。
- 保持稳定插入顺序、`source_order`、taxonomy 顺序和 JSON 字段字节。
- 完成 `integrity_check=ok`、`foreign_key_check=[]` 和契约计数后才暴露候选数据库。
- V1.18 固定 497/452/45、392/71/34，以及全部稳定字段、表和关系。

为保持 V1.18 核心数据产物字节等价，Task 8B 的 V1.18 profile 复现 legacy 已锁定的事务、`journal_mode=DELETE` 和 `VACUUM` 行为；额外只读验证不得改变文件字节。

### 9.2 CSV

- 只从最终 SQLite 的 `complete_questions_v2 ORDER BY question_id` 生成。
- 列顺序等于 SQLite 查询列顺序。
- NULL 写为空字符串，其余值使用 Python/SQLite 当前字符串表示。
- 编码固定为 UTF-8 BOM，行结束符固定为 CRLF。
- V1.18 必须为 497 行，并与 SQLite 逐列逐值一致。

### 9.3 Markdown

- 只从最终 SQLite 按 `source_order` 生成。
- 编码固定为 UTF-8，行结束符固定为 LF，文件末尾恰有一个换行。
- 每个 `question_id` 恰有一个题目标题，共 497 个唯一标题。
- 34 个 `missing_from_source` 必须显示真实缺答案标记，不生成或补写答案。

### 9.4 JSON

- 持久化证据使用 UTF-8、`ensure_ascii=False`、键排序、两空格缩进、LF 和末尾一个换行。
- 用于内部哈希的 canonical JSON 使用键排序、无多余空白和 UTF-8 编码。
- JSON 数组顺序由输入契约或稳定排序规定，不依赖 set、目录遍历或无 `ORDER BY` 查询。

### 9.5 SHA-256 与 manifest

- 摘要是文件原始字节的小写 64 位十六进制 SHA-256。
- manifest 不自哈希。
- `SHA256SUMS.txt` 覆盖 manifest 和全部受保护 payload，但不覆盖自身和包裹该 payload 的 ZIP。
- 清单按归档相对路径排序，每行固定为 `digest`、两个 ASCII 空格、相对路径和 LF。
- manifest 的键、文件集合、排除规则和 artifact kind 由 `ReleaseContract` 明确规定。

### 9.6 确定性 ZIP

- 归档路径和根目录名由 `ReleaseContract` 明确规定。
- 文件按完整归档路径排序。
- 每个条目的时间固定为 `1980-01-01 00:00:00`。
- 条目为 Unix 普通文件，权限固定 `0644`，`create_system=3`。
- 使用 DEFLATE、压缩级别 9；不写目录项、缓存、临时文件或未声明文件。
- 同一冻结输入连续构建两次，ZIP 必须逐字节一致。
- 解压到独立目录后，不依赖开发工作区即可验证哈希、SQLite、CSV、Markdown 和审计状态。

## 10. 错误模型与失败策略

异常层级：

```text
PipelineError
├── ConfigurationError
├── InputError
│   ├── InputMissingError
│   ├── InputFormatError
│   └── BaselineMismatchError
├── AuditBlockedError
├── DatabaseBuildError
│   ├── ForeignKeyViolationError
│   └── DatabaseIntegrityError
├── OutputConflictError
└── PromotionError
```

### 10.1 验证结果与异常的分界

`verify_*()` 在检查可以完整执行但产物不合格时返回 `VerificationReport(status=FAIL)`，并包含全部检查项。路径不可读、JSON 损坏、SQLite 无法打开等导致验证无法执行时抛领域异常。调用方不得通过忽略返回值继续发布；`release` 编排者必须显式要求 PASS。

### 10.2 输入失败

缺输入在任何写入前抛 `InputMissingError`；格式不可解析抛 `InputFormatError`；基线哈希、版本或 manifest 不匹配抛 `BaselineMismatchError`。这些执行错误不记为题目审计 FAIL。

### 10.3 审计和重复题

题目级问题进入 `AuditIssue`，至少包含稳定代码、严重级别、题目 ID、字段和证据。审计尽量完成并汇总所有可判断问题。精确重复使用稳定代码 `exact_duplicate`，始终为 blocker。

存在 blocker 时，`AuditResult` 仍可作为诊断证据落盘，但不能取得 `AuditedBatch`，数据库阶段抛 `AuditBlockedError`，不写候选 SQLite。

### 10.4 SQLite 失败

重复主键、外键和 integrity 错误保留相关表、键和原始检查结果。外键错误抛 `ForeignKeyViolationError`，其他完整性错误抛 `DatabaseIntegrityError`。临时数据库不能改名为候选数据库，导出阶段不得开始。

### 10.5 路径与输出冲突

所有路径先解析为绝对路径，再检查目录归属，拒绝 `..` 或符号链接越过边界。staging 和 releases 不得重叠。`audit`、`db` 和 `export` 只能写当前 staging run；只有 `promote_candidate()` 可以写 releases。

任何声明目标已存在都抛 `OutputConflictError`，且不能删除、覆盖或混合原有内容。

## 11. 行为锁定测试矩阵

### 11.1 四层测试

| 层级 | 锁定内容 | 主要断言 |
|---|---|---|
| 冻结基线回归 | V1.18 正式目录 | 文件哈希不变、verifier PASS、497/452/45、392/71/34、兼容视图存在 |
| legacy 特征测试 | Task 5/6 当前实现 | 输入顺序、审计转换、SQLite、导出格式、manifest、SHA、ZIP 和异常行为 |
| 新接口契约测试 | `audit/db/export/release` | 类型、职责隔离、领域异常、路径边界、无隐式覆盖 |
| 端到端等价测试 | 新流水线候选构建 | 核心数据产物字节一致、完整文件集、独立验证、重复构建确定性 |

### 11.2 audit

- 锁定 452 题、23 来源、唯一 ID、完整题边界和稳定顺序。
- 锁定 Task 6 的 347/71/34，以及合并 V1.17 后的 392/71/34。
- 锁定缺答案空值、2026 非官方身份、图片引用、来源哈希和 Q8 风险说明。
- 对精确重复、非法标签、缺图片、字段缺失和来源问题做多 issue 汇总。
- 存在 blocker 时不能产生 `AuditedBatch`。

### 11.3 db

- 基线哈希不符时零输出。
- V1.17 的 45 题和 Task 6 的 452 题逐字段等价。
- 历史四表与 compatibility views 保留。
- `user_version=118`、integrity `ok`、foreign-key 错误 0。
- 事务失败不暴露候选数据库。
- 重复主键、外键和 integrity 失败映射到指定领域异常。

### 11.4 export

- CSV BOM、CRLF、列顺序、NULL 表示和 497 行逐值镜像。
- Markdown 有 497 个唯一标题和 34 个缺答案标记。
- JSON 键排序、缩进、Unicode、LF 和末尾换行固定。
- 相同 SQLite 连续导出两次逐字节一致。

### 11.5 release

- manifest 文件集合与哈希闭包正确。
- SHA 清单覆盖所有受保护 payload 且不覆盖自身或 ZIP。
- ZIP 时间、权限、排序、压缩方式和归档根固定。
- 两次构建 ZIP 逐字节一致；解压后独立验证 PASS。
- 已存在 staging、ZIP 或正式目录时拒绝覆盖。
- 审批版本、审批人、范围或 candidate manifest 哈希不匹配时拒绝提升。
- 正式验证失败时不产生 `releases/<version>/`。

### 11.6 故障注入

至少覆盖缺数据库、manifest、图片，坏 JSON，基线哈希错误，精确重复，审计 blocker，重复 ID，外键错误，stale candidate，输出冲突和审批绑定错误。每项均断言异常类型、诊断证据和正式目录零变化。

## 12. Task 8B 兼容与回滚策略

### 12.1 分层等价

- `releases/V1.18/` 全目录始终逐字节不变。
- 新流水线重放产生的 SQLite、CSV、审计 JSON 和 Markdown 等核心数据产物与 legacy 产物逐字节比较。
- 因新构建器证据内容会改变，新 manifest、SHA 清单和 ZIP 不要求等于历史 ZIP 哈希；它们必须满足字段、文件集、哈希闭包、独立验证和重复构建确定性契约。
- 不通过“更新黄金哈希”处理等价性失败。

### 12.2 并行迁移边界

- legacy 文件保持不动并继续作为独立行为 oracle；新生产模块不得 import legacy。
- 新旧流水线只在临时 staging 中并行重放和比较，不写正式目录。
- compatibility tables/views 保持原名、结构和语义；删除另立任务。
- legacy 入口在 Task 8B 完成前不删除，以便代码快速回退。
- 每个新模块只有在对应新测试、54 项 legacy 回归和 V1.18 门禁同时通过后，才可成为后续新模块的依赖。

### 12.3 回滚

- 测试或等价性失败时停止迁移，继续使用 legacy oracle，并删除或隔离 disposable staging。
- 新代码按模块提交回退，不修改正式 SQLite、冻结哈希或断言。
- Task 8B 不执行正式提升，因此数据回滚目标始终是正式目录零变化。
- 未来正式发布后发现问题时，消费者切回上一正式版本；修复必须产生新版本，禁止原地修补。

## 13. 未来 CLI 调用边界

本阶段只定义边界，不实现 CLI：

```text
joy-m2 audit
joy-m2 build-db
joy-m2 export
joy-m2 verify
joy-m2 release build
joy-m2 release promote
```

CLI 只负责参数解析、仓库根发现、`PipelineConfig` 构造、结果展示和退出码映射。审计、迁移、导出、验证和发布规则全部属于 Python 模块。

退出码固定为：

- `0`：操作成功或验证 PASS。
- `1`：审计阻断、验证 FAIL 或流水线执行失败。
- `2`：参数或配置使用错误。

## 14. Task 8B 前持续门禁

每迁移一层都必须同时运行并通过：

1. Task 7：7/7。
2. Task 3–6：54/54。
3. V1.18 verifier：`PASS`。
4. 对应的新单元、集成、特征和端到端等价测试。
5. 冻结目录哈希比较。
6. `git diff` 人工检查。

任一门禁失败即停止，不能弱化断言、修改冻结哈希、删除兼容覆盖或把部分 staging 当作成功结果。

## 15. 明确不在本规格范围内

- 迁移或重写 Task 5/6 生产代码。
- 修改任何正式数据库、正式 CSV、冻结哈希或 V1.18 发布文件。
- 实现 CLI、App、API、组卷器、自动出题或 M1 功能。
- 删除 compatibility views、legacy 文件或远端备份分支。
- 设计 Task 8C。
- 未经 Joy 批准候选数据或正式提升新版本。
