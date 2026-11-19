"""
检查关联完整性：子表外键值是否都能在父表中找到。

用法：
    python local_referential_integrity.py --child cases.csv --parent person.csv \
           --child-key applicant_id --parent-key id_number

依赖：pandas。纯本地运行，不访问网络。
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from _common import load_table


def check_referential_integrity(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    child_key: str,
    parent_key: str,
) -> dict:
    child_vals = child_df[child_key].dropna()
    parent_vals = set(parent_df[parent_key].dropna())
    orphans = child_vals[~child_vals.isin(parent_vals)]
    orphan_count = len(orphans)
    total = len(child_vals)
    return {
        "子表字段": child_key,
        "父表字段": parent_key,
        "子表有效行数": total,
        "孤儿记录数": orphan_count,
        "孤儿率(%)": round(orphan_count / total * 100, 2) if total else 0.0,
        "孤儿样本": orphans.unique()[:10].tolist(),
        "状态": "FAIL" if orphan_count > 0 else "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="关联完整性检查")
    parser.add_argument("--child", required=True, help="子表文件（含外键）")
    parser.add_argument("--parent", required=True, help="父表文件（含主键）")
    parser.add_argument("--child-key", required=True)
    parser.add_argument("--parent-key", required=True)
    parser.add_argument("--encoding", help="可选：CSV 编码")
    args = parser.parse_args()

    child_df = load_table(args.child, args.encoding)
    parent_df = load_table(args.parent, args.encoding)

    for name, df, key in (("子表", child_df, args.child_key), ("父表", parent_df, args.parent_key)):
        if key not in df.columns:
            print(f"错误：{name}中不存在字段 {key}")
            sys.exit(2)

    result = check_referential_integrity(child_df, parent_df, args.child_key, args.parent_key)
    print(f"关联检查: {result['子表字段']} → {result['父表字段']}")
    print(f"  子表有效行数: {result['子表有效行数']:,}")
    print(f"  孤儿记录:     {result['孤儿记录数']:,} ({result['孤儿率(%)']}%)")
    print(f"  状态:         {result['状态']}")
    if result["孤儿样本"]:
        print(f"  孤儿样本（前 10 个，注意脱敏）: {result['孤儿样本']}")

    sys.exit(1 if result["状态"] == "FAIL" else 0)


def demo() -> None:
    parent = pd.DataFrame({"id_number": [f"11010119900101{i:04d}" for i in range(100)]})
    child = pd.DataFrame({"applicant_id": list(range(80)) + [200, 201, 202] * 10})
    result = check_referential_integrity(child, parent, "applicant_id", "id_number")
    print(f"状态: {result['状态']}，孤儿 {result['孤儿记录数']} 条 ({result['孤儿率(%)']}%)")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
