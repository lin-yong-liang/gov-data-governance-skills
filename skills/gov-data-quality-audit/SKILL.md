---
name: gov-data-quality-audit
description: 政务数据质量稽核与评分卡交付。用于按 GB/T 36344 六性对人口库、法人库、办件、共享接口等数据执行稽核，产出中文质量评分卡、HTML 稽核报告、问题清单与整改跟踪。当用户提出"做一次数据质量稽核/评估/评分卡/质量报告"，或需要核查空值、重复、跨源不一致时使用；规则体系设计请用 data-quality-engineering。
---

# 政务数据质量稽核与评分卡

## 定位与分工

- 本 skill：**执行稽核 + 出交付物**（评分卡、报告、问题清单、整改跟踪）
- `data-quality-engineering`：**设计规则体系**（规则卡、SQL 模板、评分模型方法论）

配合方式：先用规则设计 skill 定规则，再用本 skill 跑检查、打分、出报告。

## 适用场景

- 基础库/主题库上线前质量验收
- 共享数据提供前质量核验
- 季度/年度数据质量评估
- 使用方反馈数据问题后的专项稽核
- 多源比对（权威源 vs 部门数据）

## 输入清单

- 数据集：库表名、导出文件或 SQL 查询
- 主体标识：身份证号、统一社会信用代码等
- 关联关系：主键、外键、跨源关联字段
- 业务规则：值域、格式、更新周期、必填项
- 评分口径：维度权重、阈值、严重级别

## 六性与权重（GB/T 36344-2018）

| 维度 | 权重 | 检查重点 |
|---|---:|---|
| 完整性 | 25% | 必填字段空值率、数据项缺项、关联记录缺失 |
| 准确性 | 25% | 与权威源比对、业务逻辑校验、数值合理性 |
| 一致性 | 20% | 跨表总量与明细一致、跨系统状态一致、多源比对 |
| 规范性 | 15% | 身份证号、统一社会信用代码、行政区划、日期、枚举值 |
| 时效性 | 10% | 更新周期达成、T+1 就绪、接口延迟 |
| 可访问性 | 5% | 元数据完备率、接口可用率、权限可用性 |

总分 100 分：≥95 优；85–95 良；70–85 中；<70 差。

## 稽核流程

1. **明确范围与口径**：对象、时间范围、权威源、指标定义、样本量
2. **取数与留痕**：记录 SQL、执行时间、数据快照，报告必须可复现
3. **跑六类检查**：完整性、准确性、一致性、规范性、时效性、可访问性
4. **归因定级**：每条问题定位到源头（录入/接口/加工/口径），定严重级别
5. **计算得分**：维度得分 = 100 ×（1 − 违规率），总分 = Σ（权重 × 维度得分）
6. **出交付物**：评分卡、HTML 报告、问题清单
7. **整改闭环**：派单到责任部门，复核后更新状态

## 严重级别

| 级别 | 判定 | 整改时限 |
|---|---|---|
| 高 | 核心字段缺失/错误，影响共享、办件或对外发布 | 24 小时 |
| 中 | 非核心字段问题，影响分析但不影响业务办理 | 5 个工作日 |
| 低 | 展示性、格式性、个案问题 | 30 天 |

## SQL 检查模板

### 完整性：必填字段空值率

```sql
SELECT
  COUNT(*) AS total_cnt,
  SUM(CASE WHEN id_number IS NULL OR TRIM(id_number) = '' THEN 1 ELSE 0 END) AS null_cnt,
  ROUND(SUM(CASE WHEN id_number IS NULL OR TRIM(id_number) = '' THEN 1 ELSE 0 END) / COUNT(*), 6) AS null_rate
FROM dwd_population_person
WHERE dt = '${bizdate}';
```

### 规范性：身份证号 / 统一社会信用代码

```sql
-- 身份证号：18 位，末位可为 X；校验位建议用 UDF
SELECT id_number
FROM dwd_population_person
WHERE dt = '${bizdate}'
  AND (LENGTH(id_number) <> 18 OR id_number NOT RLIKE '^[0-9]{17}[0-9Xx]$')
LIMIT 100;

-- 统一社会信用代码：排除 I O S V Z，校验码按 GB 32100-2015
SELECT uscc
FROM dwd_legal_entity
WHERE dt = '${bizdate}'
  AND (LENGTH(uscc) <> 18 OR uscc NOT RLIKE '^[0-9A-HJ-NPQRTUWXY]{2}[0-9]{6}[0-9A-HJ-NPQRTUWXY]{10}$')
LIMIT 100;
```

### 一致性：多源比对（示例：死亡状态）

```sql
SELECT p.id_number, p.death_flag AS pop_flag, c.death_date
FROM dwd_population_person p
JOIN ods_civil_affairs_cremation c
  ON p.id_number = c.id_number AND c.dt = '${bizdate}'
WHERE p.dt = '${bizdate}'
  AND c.death_date IS NOT NULL
  AND (p.death_flag IS NULL OR p.death_flag = '0')
LIMIT 100;
```

### 时效性：更新延迟

```sql
SELECT MAX(dt) AS latest_dt,
       DATEDIFF(CURRENT_DATE(), MAX(dt)) AS lag_days
FROM dwd_population_person;
-- 对照目录声明更新周期，超期即问题
```

更多规则模板（主键重复、值域、关联完整性）见 `data-quality-engineering` skill。

## 本地核查脚本（数据已导出为 CSV/Parquet 时）

均在 `scripts/` 下，纯本地运行，无网络请求：

| 脚本 | 用途 |
|---|---|
| `local_null_counter.py` | 逐列空值率与阈值判定 |
| `local_duplicate_finder.py` | 全行重复、主键重复 |
| `local_referential_integrity.py` | 子表外键孤儿记录 |
| `local_value_validator.py` | 数值范围、日期范围、枚举、正则 |
| `local_freshness_check.py` | 最新记录时间与延迟 |

示例：

```bash
python scripts/local_null_counter.py --input person.csv --thresholds '{"id_number": 0}'
python scripts/local_duplicate_finder.py --input person.csv --key id_number --show-examples
python scripts/local_value_validator.py --input person.csv --rules rules.json
python scripts/local_freshness_check.py --input person.csv --timestamp-col update_time --max-lag-hours 25
```

依赖：Python 3.9+、pandas；Parquet 需 pyarrow。脚本只在本地读取指定文件，不访问网络、不写系统目录（除非显式指定 `--output`）。

## 评分卡填写

使用 `assets/quality_scorecard.md`：

- 每维度按 0–100 打分，权重按上表
- 每条发现必须写：维度、问题、涉及量、证据（SQL/样本）、责任方、级别
- 总分与评级自动对应，不手工调分
- 报告附"检查项执行清单"，未执行的项标 SKIP 并说明原因

## 交付物

- `assets/quality_scorecard.md` — 质量评分卡（一页）
- `assets/audit_report_template.html` — 稽核报告（可打印/转 PDF）
- `assets/issue_list_template.csv` — 问题清单（可导入工单系统）

## 注意事项

- 涉个人信息的样本必须脱敏，报告中不出现完整身份证号、手机号
- 不在生产库直接跑全表扫描，优先抽样或使用只读从库
- 阈值先跑 2–4 周基线再定，避免误报淹没真问题
- 多源比对前先确认权威源，不能"哪个数据多信哪个"
- 每条问题必须有责任方，否则无法闭环
- 本 skill 部分模板改编自 nimrodfisher/data-analytics-skills（MIT），详见 LICENSE
