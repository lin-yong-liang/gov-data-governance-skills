"""
检查全行重复与主键/业务键重复。

用法：
    python local_duplicate_finder.py --input person.csv --key id_number
    python local_duplicate_finder.py --input case.csv --key case_id --show-examples

依赖：pandas。纯本地运行，不访问网络。
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from _common import load_table


def find_duplicates(df: pd.DataFrame, key_cols: list[str] | None = None) -> dict:
    total = len(df)
    full_row_count = int(df.duplicated().sum())
    results = {
        "总行数": total,
        "全行重复数": full_row_count,
        "全行重复率(%)": round(full_row_count / total * 100, 2) if total else 0.0,
        "全行状态": "FAIL" if full_row_count > 0 else "PASS",
        "键检查": [],
    }

    if key_cols:
        valid_keys = [k for k in key_cols if k in df.columns]
        missing = [k for k in key_cols if k not in df.columns]
        if missing:
            results["键检查"].append({
                "键": ", ".join(missing),
                "状态": "SKIP",
                "说明": "字段不存在",
            })
        if valid_keys:
            mask = df.duplicated(subset=valid_keys, keep=False)
            dupe_rows = int(mask.sum())
            dupe_entities = int(df.loc[mask, valid_keys].drop_duplicates().shape[0])
            results["键检查"].append({
                "键": ", ".join(valid_keys),
                "重复行数": dupe_rows,
                "重复主体数": dupe_entities,
                "重复率(%)": round(dupe_rows / total * 100, 2) if total else 0.0,
                "状态": "FAIL" if dupe_rows > 0 else "PASS",
            })

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="全行与主键重复检查")
    parser.add_argument("--input", required=True)
    parser.add_argument("--key", help="逗号分隔的业务主键字段，如 id_number 或 case_id,item_id")
    parser.add_argument("--show-examples", action="store_true", help="打印重复样本（注意脱敏）")
    parser.add_argument("--encoding", help="可选：CSV 编码")
    args = parser.parse_args()

    df = load_table(args.input, args.encoding)
    key_cols = [k.strip() for k in args.key.split(",")] if args.key else None
    result = find_duplicates(df, key_cols=key_cols)

    print(f"总行数: {result['总行数']:,}")
    print(f"全行重复: {result['全行重复数']:,} ({result['全行重复率(%)']}%) [{result['全行状态']}]")
    for item in result["键检查"]:
        if item["状态"] == "SKIP":
            print(f"键 [{item['键']}]: SKIP（{item['说明']}）")
        else:
            print(f"键 [{item['键']}]: 重复行 {item['重复行数']:,}，重复主体 {item['重复主体数']:,} "
                  f"({item['重复率(%)']}%) [{item['状态']}]")

    if args.show_examples and key_cols:
        valid_keys = [k for k in key_cols if k in df.columns]
        if valid_keys:
            mask = df.duplicated(subset=valid_keys, keep=False)
            if mask.any():
                print("\n重复样本（请确认已脱敏）：")
                print(df.loc[mask].sort_values(valid_keys).head(10).to_string(index=False))

    has_fail = result["全行状态"] == "FAIL" or any(i["状态"] == "FAIL" for i in result["键检查"])
    sys.exit(1 if has_fail else 0)


def demo() -> None:
    demo_df = pd.DataFrame({
        "case_id": list(range(180)) + [5, 10, 15],
        "applicant_id": range(183),
    })
    result = find_duplicates(demo_df, key_cols=["case_id"])
    print(f"全行重复: {result['全行重复数']} [{result['全行状态']}]")
    for item in result["键检查"]:
        print(f"键重复: {item.get('重复行数')} 行 [{item['状态']}]")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
