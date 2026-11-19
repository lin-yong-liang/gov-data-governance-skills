"""
数据集画像与 PII 扫描。

输出：记录数、字段空值率、唯一值数、重复率、低基数字段分布、PII 模式匹配数量。
注意：PII 只输出匹配数量，不输出原始值；正则匹配是提示，不等于确认泄露。

用法：
    python dataset_profile.py --input dataset.csv --id-col id_number
    python dataset_profile.py --input dataset.parquet --id-col uscc --output profile.md

依赖：pandas（Parquet 需 pyarrow）。纯本地运行，不访问网络。
退出码：0 正常；1 发现主键重复或 PII 模式；2 输入错误。
"""

from __future__ import annotations

import argparse
import re
import sys

import pandas as pd

from _common import load_table

PII_PATTERNS = {
    "身份证号": r"^\d{17}[\dXx]$",
    "手机号": r"^1[3-9]\d{9}$",
    "统一社会信用代码": r"^[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}$",
}

PII_NAME_HINTS = re.compile(
    r"(^id$|_id$|id_|id_number|uscc|name|phone|mobile|address|email|证件|身份证|姓名|电话|手机|地址|邮箱)",
    re.IGNORECASE,
)


def to_markdown_table(df: pd.DataFrame) -> str:
    """不依赖 tabulate 的 Markdown 表格输出。"""
    headers = [str(col) for col in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for _, row in df.iterrows():
        values = ["" if pd.isna(row[col]) else str(row[col]) for col in df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def profile_columns(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    rows = []
    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        n = len(non_null)
        rows.append({
            "字段": col,
            "类型": str(series.dtype),
            "非空数": n,
            "空值率(%)": round((total - n) / total * 100, 2) if total else 0.0,
            "唯一值数": int(non_null.nunique()),
            "唯一率(%)": round(non_null.nunique() / n * 100, 2) if n else 0.0,
        })
    return pd.DataFrame(rows)


def scan_pii(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        values = df[col].dropna().astype(str).str.strip()
        if values.empty:
            continue
        for name, pattern in PII_PATTERNS.items():
            matched = int(values.str.match(pattern, na=False).sum())
            if matched:
                rows.append({"字段": col, "疑似类型": name, "匹配数": matched})
    return pd.DataFrame(rows)


def category_distribution(
    df: pd.DataFrame,
    max_cols: int = 5,
    top_n: int = 10,
    exclude_cols: set[str] | None = None,
) -> pd.DataFrame:
    rows = []
    used = 0
    exclude = set(exclude_cols or [])
    for col in df.columns:
        if used >= max_cols:
            break
        if col in exclude:
            continue
        non_null = df[col].notna().sum()
        nunique = df[col].nunique(dropna=True)
        # 低基数才展示；同时排除唯一率过高的标识类字段，避免泄露个人标识
        if 1 < nunique <= 20 and nunique / max(non_null, 1) <= 0.5:
            used += 1
            counts = df[col].astype(str).value_counts(dropna=False).head(top_n)
            for value, count in counts.items():
                rows.append({"字段": col, "取值": value, "记录数": int(count)})
    return pd.DataFrame(rows)


def render_markdown(
    df: pd.DataFrame,
    profile_df: pd.DataFrame,
    pii_df: pd.DataFrame,
    cat_df: pd.DataFrame,
    id_col: str | None,
    full_dup: int,
    id_dup: int | None,
) -> str:
    total = len(df)
    lines = [
        "# 数据集画像",
        "",
        "## 一、概览",
        "",
        "| 项目 | 值 |",
        "|---|---|",
        f"| 记录数 | {total:,} |",
        f"| 字段数 | {len(df.columns):,} |",
        f"| 全行重复数 | {full_dup:,} |",
        f"| 全行重复率 | {round(full_dup / total * 100, 2) if total else 0.0}% |",
    ]
    if id_col:
        lines.append(f"| 主键 `{id_col}` 重复记录数 | {id_dup:,} |")
        lines.append(f"| 主键 `{id_col}` 重复率 | {round((id_dup or 0) / total * 100, 2) if total else 0.0}% |")
    lines += ["", "## 二、字段画像", "", to_markdown_table(profile_df), ""]

    lines += ["## 三、PII 模式扫描", ""]
    if pii_df.empty:
        lines.append("未发现明显 PII 模式。注意：这只代表未命中正则，不等于数据中不存在个人信息，仍需结合字段语义判断。")
    else:
        lines.append("以下仅为模式匹配数量，未输出原始值。命中不等于确认泄露，需人工复核。")
        lines.append("")
        lines.append(to_markdown_table(pii_df))
    lines.append("")

    if not cat_df.empty:
        lines += ["## 四、低基数字段分布（前 10 值）", "", to_markdown_table(cat_df), ""]

    lines += [
        "## 五、说明",
        "",
        "- 本画像只做客观统计，不直接给出质量得分。",
        "- 质量得分需结合评测方案、阈值与人工复核，见 scorecard_template.csv。",
        "- PII 扫描仅覆盖身份证号、手机号、统一社会信用代码三类正则。",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="数据集画像与 PII 扫描")
    parser.add_argument("--input", required=True, help="CSV / Parquet 文件")
    parser.add_argument("--id-col", help="主键字段，用于重复检查")
    parser.add_argument("--output", help="输出文件：.csv 输出字段画像；其他扩展名输出 Markdown")
    parser.add_argument("--encoding", help="可选：CSV 编码")
    parser.add_argument("--top-n", type=int, default=10, help="类别分布显示前 N 个值")
    args = parser.parse_args()

    try:
        df = load_table(args.input, args.encoding)
    except Exception as exc:
        print(f"读取失败：{exc}", file=sys.stderr)
        sys.exit(2)

    if args.id_col and args.id_col not in df.columns:
        print(f"错误：主键字段 {args.id_col} 不存在", file=sys.stderr)
        sys.exit(2)

    full_dup = int(df.duplicated().sum())
    id_dup = int(df.duplicated(subset=[args.id_col]).sum()) if args.id_col else None
    profile_df = profile_columns(df)
    pii_df = scan_pii(df)
    excluded = set(pii_df["字段"].unique()) | {
        col for col in df.columns if PII_NAME_HINTS.search(str(col))
    }
    cat_df = category_distribution(df, top_n=args.top_n, exclude_cols=excluded)
    markdown = render_markdown(df, profile_df, pii_df, cat_df, args.id_col, full_dup, id_dup)

    if args.output and args.output.lower().endswith(".csv"):
        profile_df.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"字段画像已写入 {args.output}")
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"画像报告已写入 {args.output}")
    else:
        print(markdown)

    if full_dup or (id_dup or 0) > 0 or not pii_df.empty:
        if full_dup:
            print(f"\n警告：全行重复 {full_dup} 条", file=sys.stderr)
        if (id_dup or 0) > 0:
            print(f"警告：主键 {args.id_col} 重复 {id_dup} 条", file=sys.stderr)
        if not pii_df.empty:
            print(f"警告：PII 模式命中 {int(pii_df['匹配数'].sum())} 条，需人工复核", file=sys.stderr)
        sys.exit(1)


def demo() -> None:
    demo_df = pd.DataFrame({
        "id_number": ["11010119900101001X", "11010119900101002x", "11010119900101001X", "12345"],
        "name": ["张三", "李四", "张三", None],
        "phone": ["13800138000", "13900139000", "13800138000", "123456"],
        "status": ["正常", "正常", "注销", "正常"],
    })
    full_dup = int(demo_df.duplicated().sum())
    id_dup = int(demo_df.duplicated(subset=["id_number"]).sum())
    pii_demo = scan_pii(demo_df)
    excluded = set(pii_demo["字段"].unique()) | {
        col for col in demo_df.columns if PII_NAME_HINTS.search(str(col))
    }
    print(render_markdown(
        demo_df,
        profile_columns(demo_df),
        pii_demo,
        category_distribution(demo_df, exclude_cols=excluded),
        "id_number",
        full_dup,
        id_dup,
    ))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
