# Joy M2 AI Database

Joy M2 AI Database 是香港 DSE Extended Mathematics Module 2（M2）的可审计完整题题库工程。当前正式数据版本为 V1.18，共497道完整题；一道完整题一条记录，不拆分小问。

## 当前边界

- `releases/V1.18/` 是字节级锁定的只读黄金基线。
- SQLite 是唯一正式事实源；CSV、Markdown、报告和审计文件均属于正式发布资产。
- 本仓库当前只提供工程说明、依赖声明、统一验证入口和回归测试。
- 不包含 App、Web 服务、外部 API、新题生成或缺失答案补写功能。
- V1.18 发布包中的历史构建脚本和测试是发布证据；由于本目录不包含 V1.17 及更早来源工作区，它们不是当前重建入口。

## 环境

- Python 3.12.x（基准版本为 3.12.13）
- 运行时仅使用 Python 标准库
- Git

推荐在仓库根目录建立虚拟环境：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## 验证与测试

验证只读黄金基线：

```bash
python -m joy_m2 verify-baseline
```

运行全部根级回归测试：

```bash
python -m unittest discover -s tests -v
```

运行 V1.18 发布包自带的独立验证器：

```bash
python releases/V1.18/verify_task6_release.py releases/V1.18
```

三个入口均不得写入 `releases/V1.18/`。验证失败时，禁止通过修改 manifest、哈希或降低断言来绕过门禁。

## 目录

```text
.
├── AGENTS.md
├── PROJECT_CONTEXT.md
├── PROJECT_STATE.md
├── README.md
├── pyproject.toml
├── src/joy_m2/                 # 基线验证库和 CLI
├── tests/regression/           # 受保护基线回归
├── releases/V1.18/             # 只读正式发布包
└── docs/superpowers/plans/     # 已确认实施计划
```

项目事实优先级为：根级 `PROJECT_STATE.md` → V1.18 SQLite 与 `manifest.json` → 正式入库报告 → README。业务保护规则详见 `AGENTS.md` 和 `PROJECT_CONTEXT.md`。
