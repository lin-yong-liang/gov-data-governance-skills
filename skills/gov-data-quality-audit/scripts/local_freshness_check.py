"""
检查数据新鲜度：最新记录时间与当前时间的延迟是否超过阈值。

用法：
    python local_freshness_check.py --input person.csv --timestamp-col update_time --max-lag-hours 25
    python local_freshness_check.py --input person.parquet --timestamp-col etl_time --max-lag-hours 2

依赖：pandas。纯本地运行，不访问网络。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

import pandas as pd

from _common import load_table


def check_freshness(
    df: pd.DataFrame,
    timestamp_col: str,
    max_lag_hours: float = 25.0,
) -> dict:
    if timestamp_col not in df.columns:
        return {"状态": "ERROR", "说明": f"字段 {timestamp_col} 不存在"}

    ts = pd.to_datetime(df[timestamp_col], utc=True, errors="coerce")
    valid = ts.dropna()
    if valid.empty:
        return {"状态": "FAIL", "说明": "没有可用时间戳"}

    latest = valid.max()
    now = datetime.now(timezone.utc)
    lag_hours = (now - latest.to_pydatetime()).total_seconds() / 3600

    return {
        "时间字段": timestamp_col,
        "最新记录时间": latest.isoformat(),
        "当前时间": now.isoformat(),
        "延迟小时": round(lag_hours, 2),
        "阈值小时": max_lag_hours,
        "状态": "PASS" if lag_hours <= max_lag_hours else "FAIL",
        "说明": (
            f"数据新鲜，延迟 {lag_hours:.1f} 小时 ≤ {max_lag_hours} 小时"
            if lag_hours <= max_lag_hours
            else f"数据超期，延迟 {lag_hours:.1f} 小时 > {max_lag_hours} 小时"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="数据新鲜度检查")
    parser.add_argument("--input", required=True)
    parser.add_argument("--timestamp-col", required=True, help="最新更新时间字段")
    parser.add_argument("--max-lag-hours", type=float, default=25.0,
                        help="可接受最大延迟（小时），默认 25，即日更任务留 1 小时缓冲")
    parser.add_argument("--encoding", help="可选：CSV 编码")
    args = parser.parse_args()

    df = load_table(args.input, args.encoding)
    result = check_freshness(df, args.timestamp_col, args.max_lag_hours)

    for key, value in result.items():
        print(f"  {key}: {value}")

    sys.exit(0 if result["状态"] == "PASS" else 1)


def demo() -> None:
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    fresh = pd.DataFrame({"update_time": [(now - timedelta(hours=h)).isoformat() for h in range(100, 0, -1)]})
    stale = pd.DataFrame({"update_time": [(now - timedelta(hours=50)).isoformat()]})
    print("新鲜样本:", check_freshness(fresh, "update_time", 25)["状态"])
    print("超期样本:", check_freshness(stale, "update_time", 25)["状态"])


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
