# 政务数据治理 Claude Code Skills

> 仓库地址：https://github.com/lin-yong-liang/gov-data-governance-skills

面向**政务/公共数据行业**的数据治理 skill 套件，同时收录 PM/Product 通用插件，适用于 Claude Code。仓库用于个人备份、团队复用和开源分享。

## 内容总览

| 类别 | 数量 | 许可证 |
|---|---:|---|
| 政务数据治理 skill（原创） | 8 | MIT |
| 官方文档与工具 skill | 7 | Apache 2.0 |
| Composio 通用 skill | 6 | 5 个上游未提供 LICENSE，1 个 Apache 2.0 |
| PM / Product 插件 | 2 个插件包（23 个 skill 目录 + 命令/agent） | MIT |

## 一、政务数据治理 skill（8）

| Skill | 用途 | 主要交付物 |
|---|---|---|
| `data-governance-framework` | DCMM/政务数据治理评估、治理蓝图、组织与制度设计、KPI | 评估报告、路线图、制度体系 |
| `metadata-standards-master-data` | 政务信息资源目录、数据元标准、指标口径、基础库与主数据 | 目录条目、数据字典、术语表 |
| `data-quality-engineering` | 六性质量规则设计、SQL 模板、评分模型 | 规则卡、SQL 脚本、质量指标体系 |
| `data-classification-compliance` | GB/T 43697 分类分级、重要数据、共享开放、授权运营合规 | 分类分级清单、重要数据目录、脱敏方案 |
| `gov-data-quality-audit` | 质量稽核执行：评分卡、HTML 报告、问题清单、本地核查脚本 | 质量评分卡、稽核报告、整改台账 |
| `gov-data-catalog-entry` | 单个数据资源的目录条目编制、数据项清单、共享/开放属性认定 | 目录条目、数据项 CSV、元数据草稿 |
| `gov-metric-reconciliation` | 指标口径对账、差异根因分析、权威口径确认 | 对账报告、根因分析、整改建议 |
| `gov-high-quality-dataset-review` | TC609 三维度 17 项评测、抽样、标注质量、认定结论 | 评分表、评测报告、复测记录 |

## 二、官方文档与工具 skill（7）

来源：https://github.com/anthropics/skills，Apache 2.0。

| Skill | 用途 |
|---|---|
| `docx` | 创建、读取、编辑 Word 文档 |
| `pdf` | 读取、合并、拆分、填写 PDF |
| `pptx` | 创建、编辑、解析 PowerPoint |
| `xlsx` | 创建、编辑、分析 Excel |
| `doc-coauthoring` | 结构化文档协作写作 |
| `skill-creator` | 创建、修改、评测 skill |
| `mcp-builder` | 构建 MCP 服务 |

## 三、Composio 通用 skill（6）

来源：https://github.com/ComposioHQ/awesome-claude-skills。

| Skill | 用途 |
|---|---|
| `file-organizer` | 文件整理、重复文件识别（删除前确认） |
| `changelog-generator` | 从 git 提交生成 changelog |
| `content-research-writer` | 联网调研与结构化写作 |
| `connect-apps` | 连接外部 SaaS（需 Composio 插件与 API key） |
| `meeting-insights-analyzer` | 会议转写分析与沟通反馈 |
| `internal-comms` | 内部通讯、周报、FAQ、事故报告 |

> 其中 5 个 skill 上游仓库未提供 LICENSE 文件，收录状态与权利说明见 `THIRD_PARTY_NOTICES.md`。`connect-apps` 依赖 Composio 插件和 API key，当前仅收录 skill，开箱即用前需完成外部配置。

## 四、PM / Product 插件（2 个）

| 插件 | 版本 | 内容 |
|---|---|---|
| `pm-skills` | 2.14.6 | 9 个项目管理和敏捷 skill + 编排器 agent + Atlassian MCP |
| `product-skills` | 2.14.11 | 14 个产品管理 skill + 编排器 agent + discovery hook |

插件安装方式见 `plugins/README.md`。

## 安装

### 用户级 skill（21 个）

```powershell
git clone git@github.com:lin-yong-liang/gov-data-governance-skills.git
cd gov-data-governance-skills
.\install.ps1
```

或手动复制：

```powershell
Copy-Item .\skills\* "$HOME\.claude\skills\" -Recurse -Force
```

### 插件（2 个）

```powershell
.\install-plugins.ps1
```

或手动：

```powershell
claude plugin marketplace add .\plugins
claude plugin install pm-skills@gov-skill-bundle -y
claude plugin install product-skills@gov-skill-bundle -y
```

安装后重启 Claude Code 或新开会话。

## 使用示例

- “按六性给市人口库做一次质量稽核，出评分卡和问题清单”
- “给这张法人表编一份目录条目，认定共享属性”
- “大屏和月报的办件量差了 5%，帮我出一份对账报告”
- “按高质量数据集评测框架，给这个数据集出评测方案和抽样计划”
- “用 DCMM 给单位做一次数据治理现状评估”
- “用 RICE 给这批需求排优先级，并生成 PRD”

## 依赖

- Claude Code
- Python 3.10+（仅部分脚本需要）
- Python 包（按需）：`pandas`、`pyarrow`、`sqlalchemy`

```powershell
python -m pip install pandas pyarrow sqlalchemy
```

## 标准依据

- GB/T 36344-2018《信息技术 数据质量评价指标》
- GB/T 36073-2018《数据管理能力成熟度评估模型》（DCMM）
- GB/T 43697-2024《数据安全技术 数据分类分级规则》
- GB/T 21063 政务信息资源目录体系
- GB/T 39477-2020《政务信息共享 数据安全技术要求》
- 全国数标委《高质量数据集 质量评测规范》技术文件（TC609-5-2025-04）
- ISO/IEC 5259 系列《人工智能 分析与机器学习数据质量》

> 标准会更新，正式交付前请核对最新有效版本。本仓库不是官方标准文本。

## 目录结构

```
gov-data-governance-skills/
├── README.md
├── LICENSE
├── THIRD_PARTY_NOTICES.md
├── install.ps1
├── install-plugins.ps1
├── .gitignore
├── skills/                  # 21 个用户级 skill
│   ├── data-governance-framework/
│   ├── metadata-standards-master-data/
│   ├── data-quality-engineering/
│   ├── data-classification-compliance/
│   ├── gov-data-quality-audit/
│   ├── gov-data-catalog-entry/
│   ├── gov-metric-reconciliation/
│   ├── gov-high-quality-dataset-review/
│   ├── docx/ pdf/ pptx/ xlsx/
│   ├── doc-coauthoring/ skill-creator/ mcp-builder/
│   └── file-organizer/ changelog-generator/ content-research-writer/
│       connect-apps/ meeting-insights-analyzer/ internal-comms/
├── plugins/                 # PM / Product 插件包
│   ├── .claude-plugin/marketplace.json
│   ├── pm-skills/
│   ├── product-skills/
│   └── README.md
└── third_party/             # 第三方许可证与说明
```

## 许可证与第三方来源

- 本仓库原创部分：MIT，见根目录 `LICENSE`
- 第三方内容：遵循各自许可证，详见 `THIRD_PARTY_NOTICES.md`
- 收录的 Composio 5 个 skill 上游未提供 LICENSE，未声明适用本仓库 MIT 许可证

## 安全说明

- 所有脚本只读本地文件或数据库元数据，不访问外部网络
- 数据库连接串由使用者显式提供，请勿把密码写进命令行历史
- 报告和样本涉及个人信息时必须脱敏，不输出完整身份证号、手机号
- 不建议在生产库直接跑全表扫描，优先抽样或使用只读从库
- 政务数据分类分级、重要数据识别和认定结论需由本单位数据管理部门确认
- `connect-apps` 等外部 SaaS 集成在政务环境中使用前需完成安全与合规评估

## 免责声明

本仓库提供的是方法、模板和脚本，不构成官方标准或合规结论。使用者需自行核对标准的现行有效版本，并对实际数据和交付结果负责。
