"""
按业务规则校验字段值：数值/日期范围、枚举、正则。

规则 JSON 示例：
{
  "id_number":  {"pattern": "^[0-9]{17}[0-9Xx]$"},
  "uscc":       {"pattern": "^[0-9A-HJ-NPQRTUWXY]{2}[0-9]{6}[0-9A-HJ-NPQRTUWXY]{10}$"},
  "age":        {"min": 0, "max": 120},
  "reg_date":   {"min": "1900-01-01", "max": "today"},
  "gender":     {"allowed": ["1", "2", "0", "9"]}
}

用法：
    python local_value_validator.py --input person.csv --rules rules.json
    python local_value_validator.py --input person.csv --rules '{"age": {"min": 0, "max": 120}}'

依赖：pandas。纯本地运行，不访问网络。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

import pandas as pd

from _common import load_table


def _compare(series: pd.Series, value, op: str) -> pd.Series:
    """优先按数值、其次按日期、最后按字符串比较，返回布尔掩码（True 表示违规）。"""
    non_null = series.dropna()

    numeric = pd.to_numeric(non_null, errors="coerce")
    if len(non_null) > 0 and numeric.notna().all():
        try:
            target = float(value)
            return numeric < target if op == "lt" else numeric > target
        except (TypeError, ValueError):
            pass

    dates = pd.to_datetime(non_null, errors="coerce")
    if len(non_null) > 0 and dates.notna().all():
        target_ts = pd.Timestamp(date.today()) if value == "today" else pd.Timestamp(value)
        return dates < target_ts if op == "lt" else dates > target_ts

    text = non_null.astype(str)
    target_text = str(date.today()) if value == "today" else str(value)
    return text < target_text if op == "lt" else text > target_text


def validate_column(series: pd.Series, rule: dict) -> dict:
    issues = []
    total = len(series)
    non_null = series.dropna()

    if "min" in rule:
        violations = _compare(series, rule["min"], "lt")
        if int(violations.sum()) > 0:
            issues.append(f"{int(violations.sum())} 条低于下限 {rule['min']}")

    if "max" in rule:
        violations = _compare(series, rule["max"], "gt")
        if int(violations.sum()) > 0:
            issues.append(f"{int(violations.sum())} 条高于上限 {rule['max']}")

    if "allowed" in rule:
        unexpected = ~non_null.isin(rule["allowed"])
        count = int(unexpected.sum())
        if count > 0:
            sample = non_null[unexpected].astype(str).unique()[:5].tolist()
            issues.append(f"{count} 条不在枚举值域（示例: {sample}）")

    if "pattern" in rule:
        matched = non_null.astype(str).str.match(rule["pattern"], na=False)
        count = int((~matched).sum())
        if count > 0:
            sample = non_null[~matched].astype(str).unique()[:5].tolist()
            issues.append(f"{count} 条不符合正则（示例: {sample}）")

    # 空值不计入值域/格式违规，空值问题由完整性维度负责

    violation_count = 0
    if total:
        # 用规则重新统计违规行数，避免各分支重复计数
        mask = pd.Series(False, index=series.index)
        if "min" in rule:
            mask |= _compare(series, rule["min"], "lt").reindex(series.index, fill_value=False)
        if "max" in rule:
            mask |= _compare(series, rule["max"], "gt").reindex(series.index, fill_value=False)
        present = series.notna()
        if "allowed" in rule:
            mask |= present & ~series.isin(rule["allowed"])
        if "pattern" in rule:
            mask |= present & ~series.astype(str).str.match(rule["pattern"], na=False)
        violation_count = int(mask.sum())

    return {
        "状态": "FAIL" if issues else "PASS",
        "问题": "; ".join(issues) if issues else "无",
        "违规行数": violation_count,
        "违规率(%)": round(violation_count / max(total, 1) * 100, 2),
    }


def validate_ranges(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    rows = []
    for col, rule in rules.items():
        if col not in df.columns:
            rows.append({"字段": col, "规则": json.dumps(rule, ensure_ascii=False),
                         "违规行数": 0, "违规率(%)": 0, "状态": "SKIP", "问题": "字段不存在"})
            continue
        result = validate_column(df[col], rule)
        rows.append({
            "字段": col,
            "规则": json.dumps(rule, ensure_ascii=False),
            "违规行数": result["违规行数"],
            "违规率(%)": result["违规率(%)"],
            "状态": result["状态"],
            "问题": result["问题"],
        })
    return pd.DataFrame(rows)


def parse_rules(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        with open(raw, encoding="utf-8") as f:
            return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="字段值域/格式校验")
    parser.add_argument("--input", required=True)
    parser.add_argument("--rules", required=True, help="规则 JSON 字符串或文件路径")
    parser.add_argument("--output", help="可选：输出 CSV 路径")
    parser.add_argument("--encoding", help="可选：CSV 编码")
    args = parser.parse_args()

    df = load_table(args.input, args.encoding)
    result = validate_ranges(df, parse_rules(args.rules))
    print(result.to_string(index=False))

    if args.output:
        result.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"\n结果已写入 {args.output}")

    sys.exit(1 if (result["状态"] == "FAIL").any() else 0)


def demo() -> None:
    demo_df = pd.DataFrame({
        "id_number": ["11010119900101001X", "12345", "11010119900101002x", "110101199001010038"],
        "age": [30, 130, -5, 45],
        "gender": ["1", "2", "M", "0"],
    })
    rules = {
        "id_number": {"pattern": "^[0-9]{17}[0-9Xx]$"},
        "age": {"min": 0, "max": 120},
        "gender": {"allowed": ["1", "2", "0", "9"]},
    }
    print(validate_ranges(demo_df, rules).to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
