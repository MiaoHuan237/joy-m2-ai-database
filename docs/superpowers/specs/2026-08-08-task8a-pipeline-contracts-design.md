# Task 8A：统一数据流水线接口与行为锁定设计

## 1. 状态与目标

本规格记录 Task 8A brainstorming 已确认的设计。Task 8A 只梳理并锁定 legacy Task 5/6 的真实行为，定义未来 `src/joy_m2/audit/`、`src/joy_m2/db/`、`src/joy_m2/export/`、`src/joy_m2/release/` 的职责、公开接口、数据契约、错误边界、测试矩阵以及 Task 8B 的兼容与回滚策略。

本规格获 Joy 书面批准前，不生成实施计划；Task 8A 不迁移或重写生产代码。

截至 Task 8B / Task 2 Phase 2 合同修订，Phase 1 公共模型与模型测试已经
独立复审通过；本规格第 16 节冻结的是尚未实现的 Phase 2 接口与调用边界。
该修订不表示 parser、adapter、serializer、transformer、database、export 或
release 已经实现，也不授予实现权限。

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

完整数据流固定为：

```text
PipelineConfig
      ↓
explicit candidate JSON + explicit protected baseline SQLite
      ↓
audit → AuditInputEvidence → AuditResult / AuditReport → AuditedBatch
      ↓
V1.17 only: historical release transformer → V117ReleaseBatch
V1.18: AuditedBatch passes through unchanged
      ↓
db → DatabaseArtifact
      ↓
export → database-derived files + supplied audit evidence → DerivedArtifacts
      ↓
release → CandidateRelease → VerificationReport → FormalRelease
```

`release` 是唯一高层编排者；`audit`、`db` 和 `export` 互不调用。未来 CLI 可以分别调用低层接口，但不能复制业务逻辑。

### 5.1 `joy_m2.audit`

单一职责是读取显式候选 JSON 和显式受保护 baseline SQLite，检查完整题边界、字段完整性、答案身份、来源追踪、图片、标签、难度、校订和重复关系，并汇总结构化 issues 与 `AuditReport`。`audit/pipeline.py` 负责候选 JSON、文件、资源与 baseline SQLite 的存在性、类型和 SHA-256 preflight；`audit/profiles.py` 只处理已经解码的 record mapping，不访问文件系统或 SQLite。

它不修改 SQLite，不生成 CSV/Markdown，不决定正式发布，也不写 `releases/`。技术审计通过只产生 `AuditedBatch`，不等于 Joy 正式批准。

### 5.2 `joy_m2.db`

单一职责是再次验证基线身份，并把已经决定发布语义的批次事务式应用到候选 SQLite。V1.18 消费 `AuditedBatch`；V1.17 消费 `V117ReleaseBatch`。database 不拥有 publication business authority，也不得通用地创建或改写发布字段。唯一窄例外是 V1.18 frozen SQLite serialization：输入 record 必须已经精确为 `record_status="audit_passed"`，serializer 才把持久化列单向投影为 `record_status="published"`，以保持冻结 V1.18 SQLite byte-equivalence。该投影不是新的 publication decision，不修改 `AuditedRecord`、`AuditedBatch` 或 `AuditResult`，不得反向恢复 audit state，也不得用于 V1.17、未来版本、export、release orchestration 或 manifest business state。它负责 schema、metadata、import run、`user_version`、兼容对象保留、integrity 和 foreign-key 检查。

它不重新解释审计规则，不生成派生文件、manifest 或 ZIP。

### 5.3 `joy_m2.export`

单一职责是只读最终候选 SQLite，并生成 CSV、Markdown、入库报告和其他由 `ExportContract` 明确列出的数据库派生产物；同时把 audit 已经计算的 `AuditResult`/`AuditReport` 和 audit/profile 或获准 V1.17 transformer 已经映射的 records 编码、写为审计证据。

它不迁移数据库，不修改题目，不判断发布目标，也不写正式目录。它不得重新读取 candidate JSON、重新审计、重新统计 `AuditReport`，或通过 `question_id`、位置、文件顺序、对象 identity 等方式恢复记录对应关系。

### 5.4 `joy_m2.release`

单一职责是编排流水线与发布安全：创建隔离 staging run、调用 audit、V1.17 historical release transformer、database 与 export，收集审计证据 artifact，生成 manifest/SHA/ZIP、独立验证候选，以及在明确审批后原子提升。审计语义和 JSON 编码分别属于 audit 与 export；release 不重复实现。

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

Phase 2 的目标接口为：

```python
AuditRequest(
    candidate_path: Path,
    baseline_database: ArtifactRef,
    asset_root: Path,
    contract: AuditContract,
    selected_source_ids: tuple[str, ...],
)

AuditInputEvidence(
    candidate_json: ArtifactRef,
    baseline_database: ArtifactRef,
)
```

`candidate_path` 与 `baseline_database` 是两个独立、显式输入，不能从 cwd、
环境变量、仓库布局或彼此推导。pipeline 分别检查存在性、文件类型和
SHA-256。V1.17 candidate 是 Task 4 的 50/52 字段 JSON，baseline 是受保护
V1.16 SQLite；V1.18 candidate 是冻结的 452×54 字段 audited JSON，baseline
是受保护 V1.17 SQLite。preflight 以请求中的 baseline `ArtifactRef` 作为预期
identity；实际 baseline 不匹配时在任何结果构造前抛
`BaselineMismatchError`。成功完成 preflight 后，audit 创建唯一
`AuditInputEvidence` 并由 `AuditResult` 持有。`AuditResult` 包含全部 record
envelopes、issues、`AuditReport`、统计、整体状态和输入证据。存在 blocker
时，`require_passed()` 抛 `AuditBlockedError`。

以上 `AuditRequest` 和 `AuditReport` 是本次冻结但尚未实现的 Phase 2
接口；Phase 1 已实现的 `AuditedRecord`、`AuditResult.records` 和
`AuditedBatch.records` 保持不变。

### 7.2 V1.17 historical release transformer

```python
transform_v117_release(
    result: AuditResult,
    decision: V117ReleaseDecision,
) -> V117ReleaseBatch
```

该函数接收 V1.17 `AuditResult`，在函数内部首先调用 `require_passed()`，位于
audit 之后、database 写入之前。失败 result 因此抛 `AuditBlockedError`；空、
V1.18 或混合 profile 输入使用现有 `PipelineError` 边界拒绝。它不增加
provenance token、registry、identity 或平行 `passed` 布尔值。
`V117ReleaseDecision` 显式携带冻结历史发布决议；它不读取系统时钟、环境
变量、全局 registry 或 approval manifest，也不使用后续 promotion 的
`ApprovalRecord`。第 16 节冻结完整 typed envelope 与字段。

### 7.3 db

```python
build_database(request: DatabaseBuildRequest) -> DatabaseArtifact
verify_database(path: Path, contract: DatabaseContract) -> VerificationReport
```

`DatabaseBuildRequest` 对 V1.18 接受 `AuditedBatch`，对 V1.17 接受
`V117ReleaseBatch`；同时接受冻结基线、当前 staging run 内的目标路径、
`ReleaseSpec` 和 `DatabaseContract`。database 不拥有 publication business
authority。它只在 V1.18 frozen SQLite serialization boundary 接受上游精确
`record_status="audit_passed"` 并持久化为 `"published"`；除此之外不得从
audit-stage 值创建或改写发布字段。

### 7.4 export

```python
export_database(request: ExportRequest) -> DerivedArtifacts
verify_exports(request: ExportVerificationRequest) -> VerificationReport
```

正常成功路径的 Phase 2 目标 `ExportRequest` 接受已完成的
`DatabaseArtifact`、原始 `AuditResult`、与它直接对应的 `AuditedBatch` 或
获准的 `V117ReleaseBatch`、当前 staging 输出目录和 `ExportContract`。
`DerivedArtifacts` 显式列出数据库派生物和 audit evidence artifact，不返回
无约束路径字典。第 16 节冻结 record 数量、顺序和一一对应校验。

### 7.5 release

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

`CandidateBuildRequest` 的最终公共结构精确为：

```python
@dataclass(frozen=True)
class CandidateBuildRequest:
    config: PipelineConfig
    run_id: str
    release_spec: ReleaseSpec
    audit_request: AuditRequest
    v117_release_decision: V117ReleaseDecision | None
    baseline_manifest: ArtifactRef
    database_contract: DatabaseContract
    export_contract: ExportContract
    release_contract: ReleaseContract
```

所有字段均无默认值。`baseline_manifest` 对 V1.17 和 V1.18 都是必需的
typed expected identity，并原样进入 `DatabaseBuildRequest`；release 不得根据
baseline database path 查找 sibling manifest，也不得使用 filesystem discovery、
glob、legacy path、环境变量或私有额外参数取得它。V1.17 必须显式提供精确的
`V117ReleaseDecision`，并由 orchestration 原样传给
`transform_v117_release(result, request.v117_release_decision)`；不得硬编码、默认、
从 audit status/config/manifest 推断或反向恢复该 decision。V1.18 的
`v117_release_decision` 必须为 `None`，非 `None` 作为请求合同错误拒绝，且不得
因此获得任何 publication decision authority。高层构建顺序固定，但每个低层
阶段仍可单独测试。

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
- V1.17/V1.18 manifest 保持冻结 schema；输入 digest scalar 只能按第 16.3
  节从 `AuditResult.input_evidence` 单向投影。唯一例外是缺失实物的 V1.17
  正式 ZIP，它只能使用该节冻结的 historical compatibility constant。
- `artifact_sha256` 只保护生成后输出 artifact，不得承载 candidate/baseline
  输入 digest。

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

candidate/asset 输入缺失在任何写入前抛 `InputMissingError`；格式不可解析抛
`InputFormatError`。作为 expected identity 的 baseline `ArtifactRef` 所指文件
缺失，或其 kind、size、SHA-256、版本或 manifest 不匹配，统一抛
`BaselineMismatchError`。这些执行错误不记为题目审计 FAIL。

### 10.3 审计和重复题

题目级问题进入 `AuditIssue`，至少包含稳定代码、严重级别、题目 ID、字段和证据。审计尽量完成并汇总所有可判断问题。精确重复使用稳定代码 `exact_duplicate`，始终为 blocker。

存在 blocker 时，`AuditResult` 与 audit 拥有的 `AuditReport` 仍可作为诊断
证据交给 export 落盘，但不能取得 `AuditedBatch`，不得调用 transformer 或
database，也不得生成正常 candidate artifact 或进入 promotion。在
`build_candidate()` 中，失败诊断目录使用调用方显式提供的
`CandidateBuildRequest.run_id`，确定为 `data/staging/.failed/<run_id>/`；独立
audit 调用的失败证据输出位置必须由调用方显式提供，精确的独立 API 与命名
留给后续合同，不得自动生成随机 run ID 或从 cwd 推导路径。

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

- 锁定 `AuditRequest` 的 candidate JSON、baseline SQLite 两个显式输入及各自 preflight，禁止路径推导和 maintained SQLite candidate extraction。
- 锁定 452 题、23 来源、唯一 ID、完整题边界和稳定顺序。
- 锁定 Task 6 的 347/71/34，以及合并 V1.17 后的 392/71/34。
- 锁定缺答案空值、2026 非官方身份、图片引用、来源哈希和 Q8 风险说明。
- 对精确重复、非法标签、缺图片、字段缺失和来源问题做多 issue 汇总。
- 存在 blocker 时不能产生 `AuditedBatch`。
- 锁定 `AuditReport` 由 audit 计算，失败结果可诊断但不能进入 transformer/database。
- 锁定 `AuditInputEvidence` 是唯一输入证据 carrier，且所有返回 result 的
  baseline evidence 与 request `ArtifactRef` 值相等；preflight 失败零 result。
- 锁定 record-level report 公式、字符串升序 tuple keys，以及
  `issues`/result status/report status 的双向一致性。

### 11.3 V1.17 transformer

- 接受 V1.17 `AuditResult` 并在内部调用 `require_passed()`；失败 result 抛
  `AuditBlockedError`，空、V1.18 和混合输入抛 `PipelineError`。
- 锁定显式 `V117ReleaseDecision`，证明不读取时钟、环境、registry、approval manifest 或 `ApprovalRecord`。
- 每个 `V117ReleaseRecord` 直接保留一个对应 `AuditedRecord`，数量、顺序和一一对应不变。
- 通过 legacy oracle 和最终 byte-equivalence 证明 1-based `source_order` 及 53/55 字段映射。

### 11.4 db

- 基线哈希不符时零输出。
- `baseline_manifest` 必须是现有冻结 V1.17 formal manifest，不得发明新的
  profile 字段。其 identity 精确由现有字段
  `release_version="V1.17"`、`release_status="formal"`、
  `schema_version="complete-question-v1.0"` 和
  `release_model="transitional-dual-layer"` 共同定义。V1.17 build 还必须要求
  `baseline_v116_sqlite_sha256 == baseline_database.sha256`；V1.18 build 还必须
  要求 `artifact_sha256[Path(baseline_database.path).name] ==
  baseline_database.sha256`。错误、缺失或类型错误的 identity/binding 即使
  database digest 正确也必须在创建 output parent、temporary database 或
  output file 前拒绝。
- V1.17 的 45 题和 Task 6 的 452 题逐字段等价。
- 历史四表与 compatibility views 保留。
- `user_version=118`、integrity `ok`、foreign-key 错误 0。
- 事务失败不暴露候选数据库。
- 重复主键、外键和 integrity 失败映射到指定领域异常。
- V1.17 只接受 `V117ReleaseBatch`，publication values 仍完全由 V1.17
  transformer 决定；database 不得重新决定或改写 V1.17 publication semantics。
- V1.18 只接受 `AuditedBatch`。原始 typed carriers 必须保持不变；仅 frozen
  SQLite row serialization 可以把精确 `audit_passed` 单向投影为
  `published`。任何其他 source status 必须拒绝，不得任意改写。

本次 V1.18 authority remediation 获得 `INDEPENDENT REVIEW PASSED` 后，恢复
Task 4 implementation 的顺序固定为：

1. 在任何 production 修改前，先增加并运行 V1.18 frozen serialization
   compatibility projection RED。测试必须锁定上游 `audit_passed`、原始 typed
   carrier 不变、frozen V1.18 SQLite 持久化值为 `published`、projection 只发生
   在 V1.18 serialization boundary，且 V1.17 不受该例外影响。
2. 仍在任何 production 修改前，再增加并运行 manifest identity RED。至少覆盖
   correct database digest + wrong `release_version`、wrong `schema_version`、
   wrong `release_status`/`release_model`，并要求在创建 output parent、temporary
   database 或 output file 前拒绝。
3. 两组 RED 都必须证明失败来自对应 production contract 尚未实现，而不是
   setup、import、fixture 或 test construction 错误；只有确认两组正确 RED 后
   才允许修改 production。
4. production correction 只能最小闭合 V1.18 compatibility projection boundary
   和 manifest identity preflight，不得扩大 publication business authority。
5. 两组 focused tests GREEN 后，才运行完整 Task 4 regression 与 frozen
   compatibility gates。

禁止先修改 `db/profiles.py` 或 `db/pipeline.py`，再补上述 tests。resumed Task 4
必须保持 `RED → minimal fix → GREEN`。

### 11.5 export

- CSV BOM、CRLF、列顺序、NULL 表示和 497 行逐值镜像。
- Markdown 有 497 个唯一标题和 34 个缺答案标记。
- JSON 键排序、缩进、Unicode、LF 和末尾换行固定。
- 相同 SQLite 连续导出两次逐字节一致。
- audit evidence 只消费原 `AuditResult` 和直接对应 batch；数量、顺序或 envelope 不一致时零写入拒绝。
- export 不重新读取 candidate、不重新审计、不重新统计 `AuditReport`。
- export/release 不重新读取或重新哈希 candidate/baseline，不接受独立 raw
  digest，也不从 manifest scalar 反向恢复 maintained evidence。

### 11.6 release

- manifest 文件集合与哈希闭包正确。
- SHA 清单覆盖所有受保护 payload 且不覆盖自身或 ZIP。
- ZIP 时间、权限、排序、压缩方式和归档根固定。
- 两次构建 ZIP 逐字节一致；解压后独立验证 PASS。
- 已存在 staging、ZIP 或正式目录时拒绝覆盖。
- 审批版本、审批人、范围或 candidate manifest 哈希不匹配时拒绝提升。
- 正式验证失败时不产生 `releases/<version>/`。
- V1.17 调用 transformer 的位置固定在 audit result 后、database 前，并由
  transformer 内部执行 pass gate；V1.18 跳过。
- 失败审计使用调用方显式 run ID 的确定性诊断位置，不产生正常 candidate 或 promotion artifact。
- V1.17 manifest 的 `task4_candidate_sha256`、
  `baseline_v116_sqlite_sha256` 精确投影自 `AuditInputEvidence`，
  `baseline_v116_zip_sha256` 精确等于冻结历史常量；V1.18 只投影
  `baseline_v117_sqlite_sha256`，不得出现 V1.16 ZIP 字段。
- V1.17 manifest 通过 historical oracle 和 byte-equivalence；V1.18 manifest
  通过冻结 `verify_task6_release.py`，且不得新增冻结 schema 未要求的 digest
  字段或结构化 evidence 节点。

### 11.7 故障注入

至少覆盖缺数据库、manifest、图片，坏 JSON，基线哈希错误，精确重复，审计 blocker，重复 ID，外键错误，stale candidate，输出冲突和审批绑定错误。每项均断言异常类型、诊断证据和正式目录零变化。

## 12. Task 8B 兼容与回滚策略

### 12.1 分层等价

- `releases/V1.18/` 全目录始终逐字节不变。
- 新流水线重放产生的 SQLite、CSV、审计 JSON 和 Markdown 等核心数据产物与 legacy 产物逐字节比较。
- V1.17/V1.18 冻结 manifest 的字段、结构和 legacy digest scalar 必须满足
  historical oracle/byte-equivalence；不得新增结构化 evidence 节点。新构建
  运行产生的 SHA 清单和 ZIP 本身不要求复用历史 ZIP 摘要，但必须满足冻结
  文件集、哈希闭包、独立验证和重复构建确定性契约。
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

1. Task 7 historical/migrated structural and frozen-baseline gate：7/7。
2. Task 3–6：54/54。
3. V1.18 verifier：`PASS`。
4. 对应的新单元、集成、特征和端到端等价测试。
5. 冻结目录哈希比较。
6. `git diff` 人工检查。

任一门禁失败即停止，不能弱化断言、修改冻结哈希、删除兼容覆盖或把部分 staging 当作成功结果。

Task 7 的原始 7/7 结论仍是其完成时点的有效历史验收。其中
`test_task7_does_not_implement_the_task8_pipeline` 通过断言
`audit/pipeline.py`、`export/pipeline.py` 和 `release/pipeline.py` 尚不存在，
证明 Task 7 项目初始化没有提前实现 Task 8 流水线；该断言是 temporal
historical gate，不是后续 Phase 2 永久要求这些模块不存在的 architecture
invariant。Phase 2 有意改变 repository structure 后，Task 7 gate 仍保持 7 项，
但其中这一项必须按第 16.5 节先以 TDD 迁移为永久结构边界；其余 package、legacy
snapshot、V1.18 lock/hash 和独立 verifier 断言不得删除、弱化或改写历史结论。

## 15. 明确不在本规格范围内

- 迁移或重写 Task 5/6 生产代码。
- 修改任何正式数据库、正式 CSV、冻结哈希或 V1.18 发布文件。
- 实现 CLI、App、API、组卷器、自动出题或 M1 功能。
- 删除 compatibility views、legacy 文件或远端备份分支。
- 设计 Task 8C。
- 未经 Joy 批准候选数据或正式提升新版本。

## 16. Task 8B / Task 2 Phase 2 冻结合同

本节由用户审核通过，并取代本规格中把 audit candidate 模糊描述为“来源
SQLite”、把 audit evidence 写入语义归给 release、或没有 V1.17 transformer
边界的早期表述。Phase 1 的 `Task4Compatibility`、
`ReleaseCompatibility`、`AuditedRecord` 以及 records 类型迁移已经完成并
通过独立复审；本节其余类型、字段、函数和调用链均为 **DESIGN APPROVED —
NOT IMPLEMENTED**。

### 16.1 显式输入与 profile 分工

Phase 2 `AuditRequest` 精确目标结构为：

```python
@dataclass(frozen=True)
class AuditRequest:
    candidate_path: Path
    baseline_database: ArtifactRef
    asset_root: Path
    contract: AuditContract
    selected_source_ids: tuple[str, ...]

@dataclass(frozen=True)
class AuditInputEvidence:
    candidate_json: ArtifactRef
    baseline_database: ArtifactRef
```

candidate 与 baseline 是两个独立事实源。`audit/pipeline.py` 在解析 record
前分别验证 candidate JSON、baseline SQLite 和 asset root 的存在性与类型，
并重新计算两个文件的 SHA-256。candidate digest 是 observed evidence，不
存在 runtime expected candidate digest；pipeline 用实际 path、重新计算的
SHA-256、实际 `size_bytes` 和冻结 kind 构造
`AuditInputEvidence.candidate_json`。baseline request `ArtifactRef` 是 expected
identity；存在性、kind、`size_bytes` 或重新计算的 SHA-256 不匹配均在
`AuditResult` 前抛 `BaselineMismatchError`。不得从 cwd、环境变量、仓库相对位置、另一输入
路径、profile 名或全局状态推导任一输入。

`AuditInputEvidence` 是 candidate/baseline 输入证据的唯一权威 typed
carrier，并由 `AuditResult` 唯一持有。`AuditReport`、`ExportRequest`、
`DerivedArtifacts` 和其他公共模型不得保存平行 candidate/baseline digest
字段或 carrier。所有能够返回的 `AuditResult`，无论通过还是含业务 blocker，
其 `input_evidence.baseline_database` 必须与请求中的 expected
`ArtifactRef` 值相等；baseline preflight 未通过时不得构造
`AuditInputEvidence`、`AuditReport` 或 `AuditResult`。

输入职责固定为：

| Profile | Candidate | Baseline / duplicate reference | 后续 database 行为 |
|---|---|---|---|
| V1.17 | `legacy/task4_work/task4_package/03_候选数据/complete_questions_45_task4.json` 的 Task 4 audit-stage JSON，严格 50/52 字段 | 受保护 V1.16 SQLite | 从 baseline 构建并写入经 transformer 决定的 45 条 V1.17 records |
| V1.18 | `releases/V1.18/complete_questions_452_task6_audited.json`，冻结 452 条且每条 54 字段 | 受保护 V1.17 SQLite | 复制 baseline 已有 45 条正式 records，再写入 452 条 candidate records |

legacy 从 V1.17 SQLite 提取 452 条记录的逻辑只作为 characterization 与
byte-equivalence oracle，不是 maintained candidate producer，也不是第二个
candidate 真相源。`audit/profiles.py` 只接受 pipeline 已解码的单条 JSON
对象，不访问文件系统、SQLite 或哈希 API。

### 16.2 V1.17 historical release transformer

未来公共 release-stage values 精确冻结为：

```python
@dataclass(frozen=True)
class V117ReleaseDecision:
    formal_release_version: Literal["V1.17"]
    selectable: Literal[True]
    record_status: Literal["published"]
    joy_approval: Literal["approved_by_joy"]
    approved_at: Literal["2026-08-08T20:00:00+08:00"]
    schema_version: Literal["complete-question-v1.0"]

@dataclass(frozen=True)
class V117ReleaseRecord:
    audited_record: AuditedRecord
    publication_evidence: PublicationEvidence
    release_compatibility: ReleaseCompatibility
    schema_version: str

@dataclass(frozen=True)
class V117ReleaseBatch:
    records: tuple[V117ReleaseRecord, ...]

def transform_v117_release(
    result: AuditResult,
    decision: V117ReleaseDecision,
) -> V117ReleaseBatch: ...
```

transformer 必须先在内部调用 `result.require_passed()`，再验证所取得的 batch
是非空、全为 V1.17 envelope，并按输入顺序一对一产生 release records。失败
result 抛 `AuditBlockedError`；空、V1.18 或混合 envelope 输入使用现有
`PipelineError` 边界拒绝。不得增加 provenance token、registry、identity、
`passed` bool 或其他替代 `AuditResult`/`require_passed()` 的通行凭证。
每个 `V117ReleaseRecord` 直接保留对应 `AuditedRecord`；不得把
`ReleaseCompatibility` 回填到原 `AuditedRecord`，不得让两个 compatibility
carrier 同时非 `None`，也不得使用平行列表、`question_id`、列表位置、文件
顺序或对象 identity 二次拼接。

transformer 只重放受保护 legacy V1.17 的历史发布决议，不表示当前候选获得
Joy promotion 审批。它不使用 `ApprovalRecord`，不读取系统时钟、环境变量、
approval manifest 或全局 registry。`source_order` 从 1 开始并保持 record
顺序，但实现必须以 legacy oracle 和最终 byte-equivalence 证明其值，不能只
凭位置假设宣告正确。V1.18 已携带自身 release compatibility，禁止进入该
transformer。database 对 V1.17 只消费 `V117ReleaseBatch`，不能创建、默认、
规范化或改写发布字段。

`ReleaseCompatibility` 是通用 immutable value type；“V1.18-only”只约束
`AuditedRecord.release_compatibility` slot 的合法 profile 组合。独立的
`V117ReleaseRecord.release_compatibility` 可以持有 transformer 新建的
`ReleaseCompatibility`，但绝不能写回其保留的原 V1.17 `AuditedRecord`。

Phase 2 的目标 database request 为：

```python
@dataclass(frozen=True)
class DatabaseBuildRequest:
    batch: AuditedBatch | V117ReleaseBatch
    baseline_database: ArtifactRef
    baseline_manifest: ArtifactRef
    output_path: Path
    release_spec: ReleaseSpec
    contract: DatabaseContract
```

Task 3A owns the complete, closed implementation surface needed to make these
already-frozen release-stage values available before database work begins:

- modify `src/joy_m2/models.py` only to add `V117ReleaseDecision`,
  `V117ReleaseRecord`, and `V117ReleaseBatch`, and to migrate only
  `DatabaseBuildRequest.batch` from `AuditedBatch` to
  `AuditedBatch | V117ReleaseBatch`;
- modify `tests/unit/test_pipeline_models.py` only for exact field/type,
  frozen/validation/ordering/ownership tests for those three models and the
  `DatabaseBuildRequest.batch` migration;
- create `src/joy_m2/release/transformers.py`, modify
  `src/joy_m2/release/__init__.py`, and create
  `tests/unit/test_v117_release_transformer.py` for the approved transformer
  API and behavior.

Those five files are the complete Task 3A modification scope; this authority
does not extend to any other model, request field, pipeline, test, artifact, or
document. The three release models use exactly the fields and frozen semantics
above, add no convenience field or third release-batch carrier, preserve input
record order, and retain the ownership boundaries already frozen in this
section. `DatabaseBuildRequest` continues to accept `AuditedBatch`, newly
accepts `V117ReleaseBatch`, rejects every other batch type, and otherwise keeps
its field order and contract unchanged.

Task 3A uses two sequential RED/GREEN cycles. First, change only
`test_pipeline_models.py` and prove RED for the three missing release models
and the still-narrow `DatabaseBuildRequest.batch`; then make the minimal
`models.py` changes and restore the complete public-model suite to GREEN.
Second, create the focused transformer tests and prove a behavior RED caused
only by the missing approved transformer API/behavior; then implement
`release/transformers.py` and expose only that API from `release/__init__.py`.
Only after the focused Task 3A suite and the public-model, audit, Task 7, Task 6,
and V1.18 verifier regressions are GREEN may Task 3A be reviewed and committed.
The transformer must not be implemented before its public models, and its tests
must not be backfilled after production behavior.

V1.17 profile 只接受 `V117ReleaseBatch`，V1.18 profile 只接受
`AuditedBatch`；不匹配在创建输出前使用现有 `PipelineError` 边界拒绝。
Task 4 may begin only after this complete Task 3A change has passed independent
review and been committed. Task 4 consumes the already-closed
`DatabaseBuildRequest.batch: AuditedBatch | V117ReleaseBatch` contract and is
not authorized to add the release models or repeat that public-model migration.

### 16.3 audit report 与 evidence 所有权

audit 拥有 issues、`passed`/`failed`、统计、`AuditInputEvidence` 和
`AuditReport` 的语义；profile serializer
拥有 V1.17/V1.18 audit-stage record mapping，V1.17 transformer 拥有获准的
release-stage record mapping；`export/formats.py` 与 `export/pipeline.py` 拥有
JSON 表示、编码和文件写入；`release/pipeline.py` 只编排、收集
`ArtifactRef`、写 manifest/SHA、封包和验证。

未来 `AuditReport` 精确目标结构为：

```python
@dataclass(frozen=True)
class AuditReport:
    release_version: str
    status: str
    candidate_count: int
    source_count: int
    audit_passed: int
    audit_pending: int
    blocked: int
    exact_duplicate_count: int
    answer_status_counts: tuple[tuple[str, int], ...]
    image_reference_count: int
    source_counts: tuple[tuple[str, int], ...]
```

Phase 2 将 `AuditResult` 精确扩展为在现有 `status: str` 后依次增加
`report: AuditReport` 和 `input_evidence: AuditInputEvidence`。export 只能消费
已有 report/evidence，不能从 records、SQLite、candidate JSON 或 baseline
重新统计、重新读取或重新计算。成功路径的目标结构为：

```python
@dataclass(frozen=True)
class AuditResult:
    records: tuple[AuditedRecord, ...]
    issues: tuple[AuditIssue, ...]
    answer_status_counts: tuple[tuple[str, int], ...]
    status: str
    report: AuditReport
    input_evidence: AuditInputEvidence
```

`AuditResult.answer_status_counts` 与 `report.answer_status_counts` 必须相等；
保留前者是 Phase 1 公共兼容字段，不是第二个自由维护的统计来源。

```python
@dataclass(frozen=True)
class ExportRequest:
    database: DatabaseArtifact
    audit_result: AuditResult
    record_batch: AuditedBatch | V117ReleaseBatch
    output_dir: Path
    contract: ExportContract
```

该公共边界必须在任何写入前验证：

1. `audit_result.status == "passed"`，且 `record_batch` 的记录数与
   `audit_result.records` 相同；
2. `AuditedBatch.records == audit_result.records`；或对
   `V117ReleaseBatch`，按 batch 自身顺序直接取每项的 `audited_record` 后，
   其 tuple 等于 `audit_result.records`；
3. 比较是 envelope 值与顺序的直接比较，不使用对象 identity、二次关联或
   外部 registry；
4. 任一不一致使用现有 `PipelineError` 公共边界明确拒绝，不产生部分文件。

`AuditReport` 只按 successfully parsed `AuditedRecord` 计数：

- `candidate_count == len(audit_result.records)`；
- `blocked` 是具有一个或多个 blocker 的 distinct record 数，同一记录的多个
  blocker 只计一次；
- `audit_pending == 0`；
- `audit_passed == candidate_count - blocked`；
- `exact_duplicate_count` 是具有 `exact_duplicate` blocker 的 distinct record
  数；
- `answer_status_counts`、`source_counts` 和 `image_reference_count` 覆盖全部
  records；`source_count` 等于 distinct source 数；
- 两个 tuple-count 字段的 key 均按字符串升序，且只保留真实存在的正计数。

唯一状态公式为：`issues == ()` 当且仅当 `AuditResult.status == "passed"`
当且仅当 `AuditReport.status == "passed"`；`issues != ()` 当且仅当两者均为
`"failed"`。`AuditResult.status` 与 `AuditReport.status` 必须始终相等。
status 与 issues、`blocked`、`audit_passed`、records 或 envelope 的任何不一致
均抛 `PipelineError`。结构、container 或 profile 错误在结果前抛
`InputFormatError`。`audit_batch()` 的空 candidate 因 profile expected count
不符而拒绝，但公共空且无 issue 的 `AuditResult` 仍保留合法 PASS 语义。

`AuditReport.status` 是 typed 语义字段，不授权改变冻结 evidence JSON schema。
现有 V1.18 `task6_audit_report.json` 没有 `status` key；export 必须在序列化前
验证上述闭合公式，但 frozen V1.18 compatibility serializer 仍只输出历史字段，
不得新增 `status`，并须保持 byte-equivalence。V1.17 同样只按其冻结 artifact
schema 投影，不得因为公共模型新增字段而发明输出字段。manifest、report 或
record compatibility projection 都是单向序列化，不是第二个 typed carrier。

配套目标结构精确为：

```python
@dataclass(frozen=True)
class ExportContract:
    profile: str
    audit_records_filename: str
    audit_report_filename: str
    csv_filename: str
    knowledge_markdown_filename: str
    import_report_filename: str
    project_state_filename: str
    taxonomy_filename: str | None
    expected_question_count: int
    expected_missing_answer_count: int

@dataclass(frozen=True)
class DerivedArtifacts:
    csv: ArtifactRef
    knowledge_markdown: ArtifactRef
    import_report: ArtifactRef
    project_state: ArtifactRef
    taxonomy: ArtifactRef | None
    audit_records: ArtifactRef
    audit_report: ArtifactRef
```

Phase 2 输入 SHA 职责明确取代旧 Task 2 的 “real-SHA non-goal”。
`AuditReport` 不增加 digest；`ExportRequest` 和 `DerivedArtifacts` 不增加输入
evidence 或平行 digest 字段。release manifest serializer 只能从
`audit_result.input_evidence` 单向生成冻结 manifest 的历史兼容投影，不得重新
读取 candidate/baseline、重新计算其 digest、接受调用方提供的 raw digest、从
manifest scalar 反向构造 `AuditInputEvidence`，或让 carrier 与 scalar 分别
维护。冻结 V1.17/V1.18 manifest 需要逐字节等价，因此不得新增结构化
`audit_input_evidence` 节点；未来版本若采用该节点，必须另立版本化合同。

精确兼容投影为：

```text
V1.17 task4_candidate_sha256
    = audit_result.input_evidence.candidate_json.sha256
V1.17 baseline_v116_sqlite_sha256
    = audit_result.input_evidence.baseline_database.sha256
V1.18 baseline_v117_sqlite_sha256
    = audit_result.input_evidence.baseline_database.sha256
```

V1.17 还必须保留唯一专用历史常量：

```python
V117_BASELINE_V116_ZIP_SHA256: Final[str] = (
    "5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae"
)
```

并投影 `baseline_v116_zip_sha256 = V117_BASELINE_V116_ZIP_SHA256`。三个历史
权威记录——`legacy/task4_work/task3_package/05_标准规则/pre_task_hashes.json`
的 `formal_v116_package`、
`legacy/outputs/25757421d1d8/Task5_V1.17_正式入库/manifest.json` 和
`legacy/task5_work/build_task5_release.py`——一致记录该值；第一项还记录历史
制品大小为 `34_735_850` bytes。实际正式 V1.16 ZIP 已缺失，因此该常量只表示冻结
历史兼容事实；maintained pipeline 不得声称重新读取或重新验证 ZIP，也不得
从 cwd、环境、默认路径、legacy `BASE_ZIP_SHA256`、database digest 或
manifest 反向推导它。它不是 `AuditInputEvidence` 的第三个字段，不是调用方
输入，不参与 audit/database 决策，且 V1.18 manifest 禁止出现该字段。

`artifact_sha256` 继续只表示生成后的输出 artifacts 哈希集合，不得与上述输入
evidence 或历史 ZIP 常量混用。冻结 serializer 不得发明新 digest 字段；如
内部投影与 `AuditInputEvidence`、profile 或 frozen constant 不一致，必须抛
`PipelineError`，不能选择其中一个继续。

本节 authority matrix 固定为：

| 行为 | `audit/profiles.py` | `audit/pipeline.py` | V1.17 transformer | `db/pipeline.py` | `export/*` | `release/pipeline.py` |
|---|---|---|---|---|---|---|
| candidate/baseline preflight | 禁止 | **拥有** | 禁止 | baseline recheck only | 禁止 | 仅调用 |
| `AuditInputEvidence` 构造与 result ownership | 禁止 | **拥有** | 通过 result 消费 | 禁止 | 通过 result 消费 | 仅携带 result |
| report/issues/status/统计 | 禁止 | **拥有** | 禁止 | 禁止 | 只消费 | 禁止 |
| V1.17 历史发布转换 | 禁止 | 禁止 | **拥有** | 只消费 | 只消费 | 仅调用 |
| publication business authority / 通用发布字段创建或改写 | 禁止 | 禁止 | **V1.17 only** | 禁止 | 禁止 | 禁止 |
| V1.18 frozen SQLite `record_status` compatibility projection | 禁止 | 禁止 | 禁止 | **仅允许 `audit_passed` → `published` serialization** | 禁止 | 禁止 |
| database 构建 | 禁止 | 禁止 | 禁止 | **拥有** | 禁止 | 仅调用 |
| audit evidence JSON 编码/写入 | mapping only | semantics only | mapping only | 禁止 | **拥有** | 仅调用/收集 |
| evidence manifest scalar 投影 | 禁止 | evidence source only | 禁止 | 禁止 | 禁止 | **只从 result 序列化** |
| V1.17 historical ZIP constant 投影 | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 | **仅兼容序列化** |
| manifest/SHA/ZIP/候选验证 | 禁止 | 禁止 | 禁止 | 禁止 | artifact source only | **拥有** |

`ReleaseContract` deletes its existing `audit_records_filename` and
`audit_report_filename` fields; every other field retains its current order and
type. It does not repeat audit encoding semantics. release only places these
export artifacts in manifest and verification. CSV、Markdown 等数据库派生物仍
只读最终 SQLite；audit evidence 只读 `audit_result` 与 `record_batch`，两条
来源不得互相替代。

失败审计没有 `AuditedBatch`，因此不构造上述成功路径 `ExportRequest`，不
调用 transformer 或 database，也不生成正常 database/candidate artifacts。
`build_candidate()` 使用调用方显式 `run_id` 写入确定的
`data/staging/.failed/<run_id>/` 诊断位置；独立 audit evidence 的公共写入
请求和精确文件命名留给后续独立合同，但其输出目录必须由调用方显式提供。
在该合同获批前，不得暗中新增随机 run ID、时间戳目录或路径推导 API。

### 16.4 成功、失败与后续实现顺序

成功路径固定为：

```text
CandidateBuildRequest (explicit run_id, V1.17 decision-or-None, baseline manifest, and contracts)
→ AuditRequest (candidate JSON + baseline SQLite + asset root)
→ audit/pipeline preflight and JSON decoding
→ audit/profiles exact record parsing
→ duplicate seed from baseline + business audit
→ AuditInputEvidence(candidate_json, baseline_database)
→ AuditResult(AuditReport, AuditInputEvidence)
→ V1.17 only: transform_v117_release(AuditResult, decision)
  → internal require_passed() → V117ReleaseBatch
→ V1.18: require_passed() → AuditedBatch
→ build_database()
  → V1.18 frozen SQLite serialization only: `audit_passed` → `published`
    without mutating or reconstructing upstream typed state
→ export_database(database + audit_result + matching record_batch)
→ collect audit/database/export artifacts
→ release manifest serializer projects frozen scalars from AuditResult.input_evidence
  (plus V1.17-only frozen historical ZIP constant)
→ SHA-256 sums + deterministic ZIP + independent verification
→ CandidateRelease
```

失败路径固定为：input/profile 错误在 `AuditResult` 前 fail-fast；业务 blocker
产生失败 `AuditResult`/`AuditReport`，可保存确定性诊断证据，但无法取得
`AuditedBatch`，并在 transformer、database、正常 export、candidate manifest
和 promotion 前停止。

后续实现必须拆分为可独立复审的提交，推荐顺序是：Phase 2 models/contracts
测试；JSON-backed audit profiles/pipeline；V1.17 transformer；database batch
消费；typed audit evidence export；最后才是 release orchestration 和端到端
等价验证。任何一个提交都需要单独授权，本次文档提交不启动这些工作。

#### Release public carrier migration and implementation gate

Release implementation begins with a separately reviewable Public Models phase.
Its complete modification scope is limited to `src/joy_m2/models.py` and
`tests/unit/test_pipeline_models.py`, and only to the exact
`CandidateBuildRequest` migration defined in section 7.5. It may not modify any
Audit, Export, Database, Task 3A, or unrelated shared carrier.

Phase A must follow this exact TDD sequence: first modify only
`test_pipeline_models.py` and prove RED because the old carrier cannot express
the explicit V1.17 decision and typed baseline manifest; only then minimally
modify `models.py`, restore the complete Public Models suite to GREEN, obtain an
independent review, and commit that migration. Tests must lock exact field names
and order, exact annotations and runtime types, frozen behavior, absence of
defaults, rejection of invalid decision/manifest types, V1.17 requiring a
`V117ReleaseDecision`, and V1.18 requiring `None`. Both profiles require an
`ArtifactRef` baseline manifest. No hidden, default, registry, filesystem, or
private-parameter authority is permitted.

Only after the Phase A commit has passed independent review may Phase B modify
the existing Release implementation files: `release/hashing.py`,
`release/packaging.py`, `release/verification.py`, `release/pipeline.py`,
`release/__init__.py`, `test_release_primitives.py`, and
`test_release_pipeline.py`. Phase B runs Task 6 primitives RED -> GREEN before
Task 7 candidate/promotion RED -> GREEN, then focused GREEN and the complete
regression/frozen-compatibility gates. The combined Release scope is exactly
these seven files plus the two Phase A Public Models files; no other file is
implicitly authorized. Release consumes the already-reviewed Audit, Task 3A,
Database, and Export implementations and does not reimplement their authority.

#### Task 5 Export public carrier migration and implementation gate

Task 5 is the implementation owner for the remaining approved public Export
carrier migration in this design. This ownership is limited to implementing the
already-frozen `ExportContract`, `ExportRequest`, and `DerivedArtifacts` field
sets above; it does not authorize convenience fields, a parallel carrier, raw
candidate inputs, or any change to audit, database, or V1.17 transformer
authority.

The complete and closed Task 5 implementation scope is exactly:

1. `src/joy_m2/models.py`;
2. `tests/unit/test_pipeline_models.py`;
3. `src/joy_m2/export/formats.py`;
4. `src/joy_m2/export/pipeline.py`;
5. `src/joy_m2/export/__init__.py`;
6. `tests/integration/test_export_pipeline.py`.

No other file is implicitly authorized. In particular, Task 5 must first add
`audit_records_filename` and `audit_report_filename` to `ExportContract` in the
exact order defined above; add `audit_result` and
`record_batch: AuditedBatch | V117ReleaseBatch` to the single public
`ExportRequest`; and append `audit_records` and `audit_report` as `ArtifactRef`
fields to `DerivedArtifacts` while preserving the order and meaning of all
existing fields. Defaults, runtime validation, frozen semantics, and path
normalization remain governed by the existing shared-model rules and the exact
contracts in this design.

Task 5 uses two mandatory TDD phases in this order:

1. **Export Public Models RED -> GREEN.** Modify only
   `tests/unit/test_pipeline_models.py` first and prove RED for the exact three
   carrier migrations. The failure must be the old public carrier shape, not a
   test, import, setup, or unrelated regression error. Only then minimally
   modify `src/joy_m2/models.py` and restore the Public Models suite to GREEN.
2. **Export behavior RED -> GREEN.** Only after the public models are GREEN may
   Task 5 create `tests/integration/test_export_pipeline.py` and prove the
   serializer/pipeline RED while Export production behavior is still absent.
   Only then may it create `export/formats.py` and modify
   `export/pipeline.py`/`export/__init__.py` for the minimal GREEN, followed by
   the full regression and frozen-compatibility gates.

The reverse sequence -- Export production followed by public models or tests --
is forbidden. `audit_result` and `record_batch` must enter only through
`export_database(request: ExportRequest) -> DerivedArtifacts`; they cannot be
extra positional, keyword-only, private, or registry-supplied parameters. The
approved `verify_exports(request: ExportVerificationRequest) ->
VerificationReport` shape is unchanged.

Task 5 does not change the serialization contracts in sections 9.2-9.4 or the
authority rules in sections 11.5 and 16.3. `DerivedArtifacts.audit_records` and
`DerivedArtifacts.audit_report` are references only to bytes actually generated
by Export. Export may calculate SHA-256 and size for those output bytes, but it
must not recompute candidate/baseline evidence, `AuditInputEvidence`, audit
statistics, or a V1.17 release decision.

Release orchestration remains blocked until the complete Task 5 public-model and
Export behavior implementation has passed independent review and been committed.
Release must consume these completed public carriers and must not repeat or own
their migration.

### 16.5 Task 7 historical gate 的 Phase 2 迁移

`tests/regression/test_task7_project_initialization.py` 中原
`test_task7_does_not_implement_the_task8_pipeline` 只证明 Task 7 完成时没有越界
提前创建 Task 8 pipeline。它当时通过且 Task 7 的 7/7 历史结论继续有效；本次
迁移不是纠正 Task 7，而是为随后获批的 Phase 2 repository structure 替换一个
已经完成使命的时间性断言。

Phase 2 implementation 中，该单一 structural assertion 必须经过两个受控迁移
阶段；另外六项既有 Task 7 测试在两个阶段都保持不变。Stage 1 只支持前三个
scaffold 的首次创建；Stage 2 在 Task 4 首次创建 `db/pipeline.py` 前把同一断言
收紧为永久的四文件 exact-set invariant。

Stage 1 必须在创建任何 pipeline module 前，先且只把原 temporal assertion
替换为一项同时执行以下精确检查的 structural assertion：

1. `src/joy_m2/` 下名为 `pipeline.py` 的文件只允许位于：
   `audit/pipeline.py`、`db/pipeline.py`、`export/pipeline.py` 和
   `release/pipeline.py`；发现的集合必须是该 literal approved set 的 subset，
   且本次迁移后必须至少包含 `audit/pipeline.py`、`export/pipeline.py` 和
   `release/pipeline.py` 三条原冲突路径。每项必须是普通文件，不能是 symlink；
   `db/pipeline.py` 仍由后续 Task 4 的 focused TDD 首次创建，不得为本结构门禁
   提前 scaffold；任何其他文件名中含 `pipeline` 的 maintained Python module
   也禁止存在；
2. `src/joy_m2/__init__.py` 以及 `audit`、`db`、`export`、`release` 四个
   subpackage 的 `__init__.py` 必须继续存在；原
   `test_required_project_entries_exist` 保持不变；
3. 原 gate 中同样未获批准的 `src/joy_m2/db/migrate.py` 必须继续不存在；
   `src/joy_m2/cli.py`、`src/joy_m2/__main__.py` 也必须不存在，且
   `pyproject.toml` 不得出现 `[project.scripts]`；四个 approved `pipeline.py`
   只是可导入 library module，不能新增其他命令、脚本或 executable pipeline
   entry point；AST 扫描全部 `src/joy_m2/**/*.py` 时，`audit_batch` 只能定义在
   `audit/pipeline.py`，`build_database`/`verify_database` 只能定义在
   `db/pipeline.py`，`export_database`/`verify_exports` 只能定义在
   `export/pipeline.py`，`build_candidate`/`promote_candidate` 只能定义在
   `release/pipeline.py`；本阶段不授权 CLI；
4. `legacy/` 下不得存在任何文件名含 `pipeline` 的 Python module；所有已发现
   maintained pipeline module 的 AST import 必须不含顶层 `legacy` import；
   legacy 只可由测试作为 oracle 调用，不能成为 maintained runtime dependency；
5. 原 minimal legacy snapshot、V1.18 `BASELINE_LOCK.json`、release hashes、
   SQLite identity 和 embedded independent verifier 测试保持原断言与 7/7
   总数；不得以更新 frozen artifacts、hashes 或 validator 取得 GREEN。

Stage 1 的 approved set 和 required set 必须分别以四个与三个独立路径 literal
写出，不得从实际扫描结果生成期望值；此时不得要求或创建
`db/pipeline.py`。Stage 1 的 TDD 顺序冻结为：先替换 historical negative
assertion；在三个冲突 module 仍缺失时运行并看到 6 PASS/1 FAIL，且唯一失败是
required-three pipeline set 缺失；再创建三个仅含 module docstring、可直接
import 且不导出行为 API 的最小 scaffold；重跑恢复 7/7。scaffold 只建立已批准
的 package/location，不得提前
实现 audit、database、export 或 release 行为；因此后续各层必须继续先用缺失
公共函数/行为的 focused test 取得各自 RED，再修改对应 scaffold 达到 GREEN。
不得删除整个测试、把 discovered-set subset 检查放宽为未枚举路径、使用
skip/expected failure，或在测试中预先接受任意未来路径。

三文件 required set 只用于 Task 4 之前的计划过渡态。Stage 2 必须在 Task 4
首次创建 `db/pipeline.py` 前再次且只修改同一个 structural assertion：把 Stage 1
的 approved-path subset + required-three 规则升级为 discovered maintained
pipeline files 精确等于以下四文件 literal set：`audit/pipeline.py`、
`db/pipeline.py`、`export/pipeline.py`、`release/pipeline.py`。在
`db/pipeline.py` 仍不存在时运行：

```bash
$task8_python -m unittest -v tests.regression.test_task7_project_initialization
```

必须收集 7 项并得到 6 PASS/1 FAIL，
唯一失败原因必须是缺少 `db/pipeline.py`；任何其他失败都必须停止并报告合同或
实现偏差。只有确认这一 Stage 2 RED 和 Task 4 自身 focused RED 后，Task 4 才能
首次创建并最小实现 `db/pipeline.py`；Task 4 GREEN 后 Task 7 必须恢复 7/7。

从 Stage 2 GREEN 起，四文件 exact-set 关系是永久结构门禁：缺少包括
`db/pipeline.py` 在内的任何批准文件，或增加第五个 maintained pipeline module，
都必须使该 structural test 失败；Task 4 及其后任何实现不得把断言降级回 subset
或 required-three。迁移提交通过独立复审后，每个后续 Phase 2 实现层的 focused
tests 之外都必须同时重跑迁移后的 Task 7 7/7；该持续门禁和原 Task 3–6 54/54、
V1.18 verifier/frozen hash 门禁并行生效。

为执行这两个受控阶段，`tests/regression/test_task7_project_initialization.py`
明确加入 Stage 1 和 Task 4 的 approved modification scope。Stage 1 授权仅限把
上述单一 temporal assertion 替换为 subset + required-three 规则；Task 4 授权
仅限在创建 `db/pipeline.py` 前把同一断言升级为四文件 exact set。两个阶段都不得
删除、放宽或重写另外六项 Task 7 regression protection，也不得改变 frozen
boundary、legacy prohibition 或 bootstrap/package invariant。本文档修订本身仍为
docs-only，不修改测试或创建 scaffold；后续每层以及最终完整门禁运行的是 Stage 2
后的 Task 7 7/7，不重写或否定 Task 7 原历史验收记录。
