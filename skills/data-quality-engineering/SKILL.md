---
name: data-quality-engineering
description: 数据质量规则设计与质量工程（政务/公共数据视角）。用于按国标/DAMA 维度设计质量规则、生成 SQL 校验脚本（Hive/Spark/Oracle/达梦）、质量评分与报告、共享数据质量监测与问题闭环机制设计。当用户提到数据质量、质量规则、数据校验、数据稽核、质量报告、空值/重复/一致性检查、多源比对时使用。
---

# 数据质量工程（政务/公共数据）

## 质量维度（GB/T 36344-2018，常用六性）

| 维度 | 含义 | 政务典型规则 |
|---|---|---|
| 规范性 | 符合标准与格式要求 | 身份证号 18 位、统一社会信用代码格式、行政区划代码 |
| 完整性 | 必填项不缺失 | 关键字段空值率、数据项缺项 |
| 准确性 | 与真实值一致 | 与权威源比对、业务逻辑校验 |
| 一致性 | 跨表/跨系统一致 | 人口库与民政/人社数据一致、总数=分项之和 |
| 时效性 | 按时更新可用 | 目录更新周期达成、接口 T+1 就绪 |
| 可访问性 | 可获取可理解 | 接口可用率、元数据完备率 |

政务数据质量的特殊性：多源比对是主要手段（权威源 vs 部门数据），"鲜活度"是核心指标。

## 规则设计卡模板

| 字段 | 说明 |
|---|---|
| 规则编号 | DQ-{域}-{序号}，如 DQ-POP-001 |
| 检核对象 | 库.表 / 字段 / 跨表 / 跨库 |
| 质量维度 | 六性之一 |
| 规则描述 | 一句话业务化描述 |
| SQL 逻辑 | 可执行脚本 |
| 阈值 | 如 空值率 ≤ 0.1% |
| 严重级别 | 高/中/低（决定告警与整改时限） |
| 责任方 | 权威源部门 / 数据提供方 |
| 检核频率 | 日/周/月 |

## SQL 模板（Hive/Spark SQL）

### 完整性：关键字段空值率

```sql
SELECT
  COUNT(*) AS total_cnt,
  SUM(CASE WHEN id_number IS NULL OR TRIM(id_number) = '' THEN 1 ELSE 0 END) AS null_cnt,
  ROUND(SUM(CASE WHEN id_number IS NULL OR TRIM(id_number) = '' THEN 1 ELSE 0 END) / COUNT(*), 6) AS null_rate
FROM dwd_population_person
WHERE dt = '${bizdate}';
```

### 唯一性：主体标识重复

```sql
SELECT id_number, COUNT(*) AS cnt
FROM dwd_population_person
WHERE dt = '${bizdate}'
GROUP BY id_number
HAVING COUNT(*) > 1
LIMIT 100;
```

### 规范性：身份证号格式

```sql
SELECT id_number
FROM dwd_population_person
WHERE dt = '${bizdate}'
  AND (LENGTH(id_number) <> 18 OR id_number NOT RLIKE '^[0-9]{17}[0-9Xx]$')
LIMIT 100;
-- 校验位计算建议用 UDF 实现（GB 11643）
```

### 规范性：统一社会信用代码格式

```sql
SELECT uscc
FROM dwd_legal_entity
WHERE dt = '${bizdate}'
  AND (LENGTH(uscc) <> 18 OR uscc NOT RLIKE '^[0-9A-HJ-NPQRTUWXY]{2}[0-9]{6}[0-9A-HJ-NPQRTUWXY]{10}$')
LIMIT 100;
-- 字符集排除 I O S V Z，校验码按 GB 32100-2015
```

### 一致性：跨库多源比对（死亡状态）

```sql
SELECT p.id_number, p.death_flag AS pop_death_flag, c.death_date
FROM dwd_population_person p
JOIN ods_civil_affairs_cremation c
  ON p.id_number = c.id_number AND c.dt = '${bizdate}'
WHERE p.dt = '${bizdate}'
  AND c.death_date IS NOT NULL
  AND (p.death_flag IS NULL OR p.death_flag = '0')
LIMIT 100;
-- 民政火化数据与人口库死亡标识不一致，需回流权威源核实
```

### 关联完整性：办件申请主体缺失

```sql
SELECT f.case_id, f.applicant_id
FROM dwd_gov_service_case f
LEFT JOIN dim_population_person p
  ON f.applicant_type = '1' AND f.applicant_id = p.id_number AND p.dt = '${bizdate}'
LEFT JOIN dim_legal_entity l
  ON f.applicant_type = '2' AND f.applicant_id = l.uscc AND l.dt = '${bizdate}'
WHERE f.dt = '${bizdate}'
  AND p.id_number IS NULL
  AND l.uscc IS NULL
LIMIT 100;
```

### 时效性：数据就绪与更新延迟

```sql
SELECT MAX(dt) AS latest_dt,
       DATEDIFF(CURRENT_DATE(), MAX(dt)) AS lag_days
FROM dwd_population_person;
-- 对照目录声明的更新周期，超期触发告警
```

Oracle/达梦版替换日期函数（`TRUNC(SYSDATE)`、`SYSDATE - 1`）与分区条件；正则改用 `REGEXP_LIKE`。

## 评分模型

质量得分 = Σ(维度权重 × 维度得分)，维度得分 = 100 × (1 − 违规率)，违规率需设基线。

参考权重（可按业务调整）：完整性 25%、准确性 25%、一致性 20%、规范性 15%、时效性 10%、可访问性 5%。
评级：≥95 优；85–95 良；70–85 中；<70 差。

## 质量报告结构

1. 本期概览（总得分、环比、规则覆盖数、涉及部门）
2. 分维度得分与趋势
3. 重点问题 TOP N（问题、涉及量、影响业务、责任部门）
4. 整改跟踪（上期问题闭环情况、超期未整改通报）
5. 共享接口质量（调用成功率、响应时长、返回准确率）
6. 附录（规则明细与执行日志）

## 问题闭环

发现（自动检核/使用方反馈）→ 定级派单 → 根因分析（源头录入/接口/加工/口径）→ 责任部门整改 → 复核验证 → 知识库沉淀。

关键机制：问题单与责任部门绑定、超时升级、闭环率纳入考核；跨部门争议由数据局裁定。

## 注意事项

- 阈值先跑 2–4 周基线再定，避免大量误报
- 规则要业务化命名，避免"表字段级"技术描述
- 优先覆盖基础库和核心共享数据（人口、法人、证照、办件）
- 质量前移：源头录入校验优于事后检核
- 多源比对发现的问题，需明确以哪个权威源为准
