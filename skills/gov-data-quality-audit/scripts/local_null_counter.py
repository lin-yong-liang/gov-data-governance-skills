"""
逐列统计空值率，并按预警/失败阈值判定。

用法：
    python local_null_counter.py --input person.csv
    python local_null_counter.py --input person.csv --thresholds '{"id_number": 0, "phone": 1}'
    python local_null_counter.py --input person.parquet --output null_report.csv

依赖：pandas（Parquet 需 pyarrow）。
纯本地运行，不访问网络。
"""

from __future__ import annotations

import argparse
import json
import sys

import pandas as pd

from _common import load_table

DEFAULT_WARN_PCT = 5.0
DEFAULT_FAIL_PCT = 20.0


def parse_thresholds(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        with open(raw, encoding="utf-8") as f:
            return json.load(f)


def count_nulls(
    df: pd.DataFrame,
    thresholds: dict | None = None,
    default_warn: float = DEFAULT_WARN_PCT,
    default_fail: float = DEFAULT_FAIL_PCT,
) -> pd.DataFrame:
    thresholds = thresholds or {}
    rows = []
    total = len(df)
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = round(null_count / total * 100, 2) if total else 0.0
        fail_thresh = float(thresholds.get(col, default_fail))
        warn_thresh = float(min(thresholds.get(col, default_warn), fail_thresh))

        if null_pct > fail_thresh:
            status = "FAIL"
        elif null_pct > warn_thresh:
            status = "WARN"
        else:
            status = "PASS"

        rows.append({
            "字段": col,
            "类型": str(df[col].dtype),
            "空值数": null_count,
            "空值率(%)": null_pct,
            "预警阈值(%)": warn_thresh,
            "失败阈值(%)": fail_thresh,
            "状态": status,
        })
    return pd.DataFrame(rows).sort_values("空值率(%)", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="逐列空值率检查")
    parser.add_argument("--input", required=True, help="CSV / Parquet 文件路径")
    parser.add_argument("--thresholds", default="{}", help="JSON 字典或 JSON 文件：字段 -> 可接受空值率(%)")
    parser.add_argument("--warn-pct", type=float, default=DEFAULT_WARN_PCT)
    parser.add_argument("--fail-pct", type=float, default=DEFAULT_FAIL_PCT)
    parser.add_argument("--output", help="可选：输出 CSV 路径")
    parser.add_argument("--encoding", help="可选：CSV 编码，如 utf-8-sig 或 gbk")
    args = parser.parse_args()

    df = load_table(args.input, args.encoding)
    result = count_nulls(df, thresholds=parse_thresholds(args.thresholds),
                         default_warn=args.warn_pct, default_fail=args.fail_pct)

    print(result.to_string(index=False))
    fails = result[result["状态"] == "FAIL"]
    if not fails.empty:
        print(f"\n共 {len(fails)} 个字段未通过：")
        for _, row in fails.iterrows():
            print(f"  {row['字段']}: 空值率 {row['空值率(%)']}%（阈值 {row['失败阈值(%)']}%）")

    if args.output:
        result.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"\n结果已写入 {args.output}")

    sys.exit(1 if not fails.empty else 0)


def demo() -> None:
    import numpy as np

    rng = np.random.default_rng(10)
    demo_df = pd.DataFrame({
        "id_number": [None if rng.random() < 0.02 else f"11010119900101{i:04d}" for i in range(200)],
        "name": [None if rng.random() < 0.01 else "张三" for _ in range(200)],
        "address": [None if rng.random() < 0.30 else "北京市东城区" for _ in range(200)],
    })
    print(count_nulls(demo_df, thresholds={"id_number": 0}).to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
