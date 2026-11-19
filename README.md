# 政务数据治理 Claude Code Skills

面向**政务/公共数据行业**的数据治理 skill 套件，适用于 Claude Code。覆盖治理体系评估、政务数据目录、数据质量、分类分级与合规、高质量数据集评测等场景。

## Skill 一览

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

## 安装

### 方式一：脚本（推荐）

```powershell
git clone git@github.com:<your-name>/gov-data-governance-skills.git
cd gov-data-governance-skills
.\install.ps1
```

### 方式二：手动复制

```powershell
Copy-Item .\skills\* "$HOME\.claude\skills\" -Recurse -Force
```

安装后重启 Claude Code 或新开会话，skill 会自动加载。

## 使用示例

- “按六性给市人口库做一次质量稽核，出评分卡和问题清单”
- “给这张法人表编一份目录条目，认定共享属性”
- “大屏和月报的办件量差了 5%，帮我出一份对账报告”
- “按高质量数据集评测框架，给这个数据集出评测方案和抽样计划”
- “用 DCMM 给单位做一次数据治理现状评估”

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
├── install.ps1
├── .gitignore
└── skills/
    ├── data-governance-framework/
    ├── metadata-standards-master-data/
    ├── data-quality-engineering/
    ├── data-classification-compliance/
    ├── gov-data-quality-audit/
    ├── gov-data-catalog-entry/
    ├── gov-metric-reconciliation/
    └── gov-high-quality-dataset-review/
```

## 安全说明

- 所有脚本只读本地文件或数据库元数据，不访问外部网络。
- 数据库连接串由使用者显式提供，请勿把密码写进命令行历史。
- 报告和样本涉及个人信息时必须脱敏，不输出完整身份证号、手机号。
- 不建议在生产库直接跑全表扫描，优先抽样或使用只读从库。
- 政务数据分类分级、重要数据识别和认定结论需由本单位数据管理部门确认。

## 许可证

MIT License。部分模板结构参考 `nimrodfisher/data-analytics-skills`（MIT），详见相关 skill 下的 `LICENSE` 文件。

## 免责声明

本仓库提供的是方法、模板和脚本，不构成官方标准或合规结论。使用者需自行核对标准的现行有效版本，并对实际数据和交付结果负责。
