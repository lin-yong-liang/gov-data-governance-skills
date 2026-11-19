"""本地脚本公共函数。纯本地读取，不访问网络。"""

from __future__ import annotations

import pandas as pd


def read_csv_auto(path: str, encoding: str | None = None) -> pd.DataFrame:
    if encoding:
        return pd.read_csv(path, encoding=encoding)
    last_error: Exception | None = None
    for enc in ("utf-8-sig", "gbk"):
        try:
            return pd.read_csv(path, encoding=enc)
        except (UnicodeDecodeError, UnicodeError) as exc:
            last_error = exc
    if last_error:
        raise last_error
    return pd.read_csv(path)


def load_table(path: str, encoding: str | None = None) -> pd.DataFrame:
    lower = path.lower()
    if lower.endswith((".csv", ".txt")):
        return read_csv_auto(path, encoding)
    if lower.endswith(".parquet"):
        return pd.read_parquet(path)
    raise ValueError("仅支持 CSV / TXT / Parquet；数据库数据请用 SQL 或导出后核查")
